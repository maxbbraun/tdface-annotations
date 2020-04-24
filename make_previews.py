from absl import app
from absl import flags
from absl import logging
import csv
import cv2
import os

FLAGS = flags.FLAGS
flags.DEFINE_string('tdface_dir', None, 'The directory with the unzipped '
                    'Tufts Face Database images.')
flags.DEFINE_string('bounding_boxes', None, 'The path to the bounding boxes '
                    'CSV file.')
flags.DEFINE_string('previews_dir', None, 'The directory to hold the preview '
                    'images.')

LINE_COLOR = (0, 255, 0)
LINE_WIDTH = 1


def main(_):
    # Turn the bounding boxes CSV into a dictionary.
    bounding_boxes = {}
    with open(FLAGS.bounding_boxes, newline='') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip header.

        for row in reader:
            key = os.path.join(str(row[1]), str(row[2]))
            bounding_box = list(map(int, row[3:]))
            bounding_boxes[key] = bounding_box

    # Create annotated versions of all images.
    for root, _, files in os.walk(FLAGS.tdface_dir):
        for filename in files:
            if filename.endswith('.jpg'):
                _, set_dir, participant = root.split(os.sep)
                key = os.path.join(participant, filename)
                bounding_box = bounding_boxes[key]
                top_left = (bounding_box[0], bounding_box[1])
                bottom_right = (bounding_box[0] + bounding_box[2],
                                bounding_box[1] + bounding_box[3])

                image_path = os.path.join(root, filename)
                image = cv2.imread(image_path)
                cv2.rectangle(image, top_left, bottom_right, LINE_COLOR,
                              LINE_WIDTH)

                save_dir = os.path.join(FLAGS.previews_dir, set_dir,
                                        participant)
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, filename)
                cv2.imwrite(save_path, image)
                logging.info('Saved: %s' % save_path)


if __name__ == '__main__':
    app.run(main)
