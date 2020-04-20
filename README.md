# Tufts Face Database Annotations

Ground truth annotations for the [Tufts Face Database](https://github.com/maxbbraun/Tufts-Face-Database-Annotations)

| Modality | Annotations |
| --- | --- |
| [TD_3D](http://tdface.ece.tufts.edu/downloads/TD_3D/) | N/A |
| [TD_CS](http://tdface.ece.tufts.edu/downloads/TD_CS/) | N/A |
| [TD_IR_A](http://tdface.ece.tufts.edu/downloads/TD_IR_A/) | [bounding-boxes.csv](bounding-boxes.csv) |
| [TD_IR_E](http://tdface.ece.tufts.edu/downloads/TD_IR_E/) | [bounding-boxes.csv](bounding-boxes.csv) |
| [TD_LYT_A](http://tdface.ece.tufts.edu/downloads/TD_LYT_A/) | N/A |
| [TD_NIR_A](http://tdface.ece.tufts.edu/downloads/TD_NIR_A/) | N/A |
| [TD_RGB_A](http://tdface.ece.tufts.edu/downloads/TD_RGB_A/) | N/A |
| [TD_RGB_E](http://tdface.ece.tufts.edu/downloads/TD_RGB_E/) | N/A |
| [TD_VIDEO](http://tdface.ece.tufts.edu/downloads/TD_VIDEO.zip) | N/A |

## Method

1. Download the raw images from the [database](http://tdface.ece.tufts.edu/downloads/):
```
for i in $(seq 1 4)
do
  curl -O http://tdface.ece.tufts.edu/downloads/TD_IR_A/TD_IR_A_Set$i.zip
  curl -O http://tdface.ece.tufts.edu/downloads/TD_IR_E/TD_IR_E_Set$i.zip
done
```

2. Host the images using [Google Cloud Storage](https://cloud.google.com/storage):
```
BUCKET_NAME="tufts-face-database"
BUCKET="gs://$BUCKET_NAME"

mkdir $BUCKET_NAME
for f in TD_IR_*.zip
do
  unzip $f -d $BUCKET_NAME/$(basename $f .zip)
done

gsutil mb -l us-central1 $BUCKET
gsutil -m rsync -r tufts-face-database $BUCKET
gsutil iam ch allUsers:objectViewer $BUCKET
```

3. Set up a callback server using [Node.js and MongoDB on Heroku](https://github.com/scaleapi/sample-callback-server-node).

4. Create the [Scale](https://scale.com) annotation tasks:
```
SCALE_API_KEY="<Live API Key from Scale dashboard>"
SCALE_PROJECT="tufts_face_database"
CALLBACK_URL="https://scale-callback-server.herokuapp.com/"
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
done
```

5. Check the [Scale Dashboard](https://dashboard.scale.com/) for the annotation tasks to be completed.

6. Export the annotations as a CSV file:
```
mongoexport \
  --host=<Host from Heroku/mLab dashboard> \
  --db=<Database name from Heroku/mLab dashboard> \
  --collection=tasks \
  --username=<User from Heroku/mLab dashboard> \
  --out=bounding-boxes.csv \
  --type=csv \
  --fields=params.attachment,response.annotations \
  --sort='{"params.attachment": 1}'

sed -E -i '' "s/params\.attachment,response\.annotations/Set,Participant,File,Left,Top,Width,Height/" bounding-boxes.csv
sed -E -i '' "s/^https:\/\/storage.googleapis.com\/$BUCKET_NAME\/(.+)\/(.+)\/(.+),\"\[{.+\"\"top\"\":(.+),\"\"left\"\":(.+),\"\"label\"\":\"\"face\"\",\"\"height\"\":(.+),\"\"width\"\":(.+)}\]\"$/\1,\2,\3,\5,\4,\7,\6/" bounding-boxes.csv
```
