# Tufts Face Database Annotations

Ground truth annotations for the [Tufts Face Database](https://github.com/kpvisionlab/Tufts-Face-Database).

| Modality | Annotations |
| - | - |
| [TD_3D](http://tdface.ece.tufts.edu/downloads/TD_3D/) | N/A |
| [TD_CS](http://tdface.ece.tufts.edu/downloads/TD_CS/) | N/A |
| [TD_IR_A](http://tdface.ece.tufts.edu/downloads/TD_IR_A/) | [bounding-boxes.csv](https://github.com/maxbbraun/tdface-annotations/releases/latest/download/bounding-boxes.csv) |
| [TD_IR_E](http://tdface.ece.tufts.edu/downloads/TD_IR_E/) | [bounding-boxes.csv](https://github.com/maxbbraun/tdface-annotations/releases/latest/download/bounding-boxes.csv) |
| [TD_LYT_A](http://tdface.ece.tufts.edu/downloads/TD_LYT_A/) | N/A |
| [TD_NIR_A](http://tdface.ece.tufts.edu/downloads/TD_NIR_A/) | N/A |
| [TD_RGB_A](http://tdface.ece.tufts.edu/downloads/TD_RGB_A/) | N/A |
| [TD_RGB_E](http://tdface.ece.tufts.edu/downloads/TD_RGB_E/) | N/A |
| [TD_VIDEO](http://tdface.ece.tufts.edu/downloads/TD_VIDEO.zip) | N/A |

## License

Only the annotation data ([bounding-boxes.csv](https://github.com/maxbbraun/tdface-annotations/releases/latest/download/bounding-boxes.csv)) is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/) license.

The original terms and conditions of the [Tufts Face Database](http://tdface.ece.tufts.edu/) apply to the images:

> Researcher shall use the Database only for non-commercial research and educational purposes. Any commercial distribution or act related to the commercial usage of this database is strictly prohibited. Tufts University nor Panetta’s Vision and Sensing System Lab makes no representations or warranties regarding the Database, including but not limited to warranties of non-infringement or fitness for a particular purpose. The Researcher may not provide research associates and colleagues with access to the Database. The distribution of this database to any parties that have not read and agreed to the terms and conditions of usage is strictly prohibited. Researcher accepts full responsibility for his or her use of the Database and shall defend and indemnify the Tufts University or the Panetta’s Vision and Sensing System Lab, including their employees, Trustees, officers and agents, against any and all claims arising from Researcher's use of the Database, including but not limited to Researcher's use of any copies of copyrighted images that he or she may create from the Database. Neither Panetta’s vision and sensing systems lab nor any third parties who may provide information to us for the dissemination purpose shall have any responsibility for or be liable in respect of the content or the accuracy of the provided information, or for any errors or omissions therein. The Panetta’s vision and sensing systems lab reserves the right to revise, amend, alter or delete the information provided herein at any time, but shall not be responsible for or liable in respect of any such revisions, amendments, alterations or deletions. The images available in this database can only be published or presented in research papers or at research conferences and cannot be used for any commercial purpose. No permission is granted to reproduce the database or post into any webpage or any other storage means. This database contains human subjects who agreed to participate in the acquisition of this database for the research purposes. To guarantee the proper use of this database, the above steps are requested and must be followed by every user. No country or institution is excluded of any of the above steps. Failure to follow the above steps will invite legal prosecution.

## Method

#### 1. Download the raw images from the [database](http://tdface.ece.tufts.edu/downloads/):
```bash
for i in $(seq 1 4)
do
  curl -O http://tdface.ece.tufts.edu/downloads/TD_IR_A/TD_IR_A_Set$i.zip
  curl -O http://tdface.ece.tufts.edu/downloads/TD_IR_E/TD_IR_E_Set$i.zip
  # TODO: Support the other modalities.
done
```

#### 2. Host the images using [Google Cloud Storage](https://cloud.google.com/storage):
```bash
BUCKET_NAME=""  # Insert globally unique name.
BUCKET="gs://$BUCKET_NAME"

mkdir $BUCKET_NAME
for f in TD_IR_*.zip
do
  unzip $f -d $BUCKET_NAME/$(basename $f .zip)
done

gsutil mb -l us-central1 $BUCKET
gsutil -m rsync -r $BUCKET_NAME $BUCKET
gsutil iam ch allUsers:objectViewer $BUCKET
```

#### 3. Set up a callback server using [Node.js and MongoDB on Heroku](https://github.com/scaleapi/sample-callback-server-node).

#### 4. Create the [Scale](https://scale.com) annotation tasks:
```bash
SCALE_API_KEY=""  # Insert "Live API Key" from Scale dashboard.
SCALE_PROJECT=""  # Insert project name from Scale dashboard.
CALLBACK_URL=""  # Insert callback server URL from step 3.
INSTRUCTION="Draw a box around each face. The top should be above the forehead. The bottom should be below the chin. The left and right should span the width of the face, ignoring ears."

for f in $(gsutil ls -r $BUCKET/**/*.jpg)
do
  path=$(printf '%s\n' "${f//$BUCKET\//}")
  url="https://storage.googleapis.com/$BUCKET_NAME/$path"
  curl "https://api.scale.com/v1/task/annotation" \
    -u "$SCALE_API_KEY:" \
    -d callback_url="$CALLBACK_URL" \
    -d instruction="$INSTRUCTION" \
    -d attachment_type=image \
    -d attachment="$url" \
    -d objects_to_annotate[0]="face" \
    -d with_labels=false \
    -d project="$SCALE_PROJECT"
  # TODO: Add face landmark annotations.
done
```

#### 5. Check the [Scale Dashboard](https://dashboard.scale.com) for all annotation tasks to be completed.

#### 6. Export the annotations as a CSV file:
```bash
MONGO_HOST=""  # Insert database host from Heroku/mLab dashboard.
MONGO_DB=""  # Insert database name from Heroku/mLab dashboard.
MONGO_USER=""  # Insert database user from Heroku/mLab dashboard.
CSV_FILE="bounding-boxes.csv"

mongoexport \
  --host=$MONGO_HOST \
  --db=$MONGO_DB \
  --collection=tasks \
  --username=$MONGO_USER \
  --out=$CSV_FILE \
  --type=csv \
  --fields=params.attachment,response.annotations \
  --sort='{"params.attachment": 1}'

sed -E -i '' "s/params\.attachment,response\.annotations/Set,Participant,File,Left,Top,Width,Height/" $CSV_FILE
sed -E -i '' "s/^https:\/\/storage.googleapis.com\/$BUCKET_NAME\/(.+)\/(.+)\/(.+),\"\[{.+\"\"top\"\":(.+),\"\"left\"\":(.+),\"\"label\"\":\"\"face\"\",\"\"height\"\":(.+),\"\"width\"\":(.+)}\]\"$/\1,\2,\3,\5,\4,\7,\6/" $CSV_FILE
sort -t, -k 2 -n $CSV_FILE -o $CSV_FILE
```

#### 7. Create previews
```bash
PREVIEWS_DIR=previews

python3 -m venv venv && . venv/bin/activate
pip install opencv-python absl-py

python make_previews.py --tdface_dir=$BUCKET_NAME --bounding_boxes=$CSV_FILE --previews_dir=$PREVIEWS_DIR
```

#### 8. Clean up
```bash
rm TD_*.zip
rm -rf $BUCKET_NAME
gsutil rm -r $BUCKET
```
