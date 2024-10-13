import os
import imagehash
from PIL import Image

image_hash_dict = {}
def is_duplicate(image_hash, cutoff=10):
    global image_hash_dict
    duplicate = []
    for hash_value in image_hash_dict:
        if image_hash - hash_value <= cutoff:
            duplicate.append(image_hash_dict[hash_value])
    return duplicate


def similar_image(image_directory, hash_size=16, cutoff=100):
    for filename in os.listdir(image_directory):
        if filename.endswith(('png', 'jpg', 'jpeg', 'bmp', 'jfif', 'webp')):
            image_path = os.path.join(image_directory, filename)
            image = Image.open(image_path)
            gray_image = image.convert('L')
            gray_image = gray_image.resize((1000, 1000))
            image_hash = imagehash.phash(gray_image, hash_size=hash_size)

            duplicate = is_duplicate(image_hash, cutoff)
            if duplicate:
                print(f'Duplicate image found: {filename} with {duplicate}')
                # Open image file
                image = Image.open(image_path)
                image.show()
                image = Image.open(os.path.join(image_directory, duplicate[0]))
                image.show()
                input('Press Enter to continue...')
            else:
                image_hash_dict.update({image_hash: filename})

directory = r'D:\Downloads\New Product'
similar_image(directory)