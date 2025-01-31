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
                print('Type d/del to delete the image & press enter to continue: ', end='')
                if input().lower() in ['d', 'del']:
                    all_duplicate_file_list = duplicate + [filename]
                    highest_image_size = 0
                    highest_image_path = ''
                    for duplicate_file in all_duplicate_file_list:
                        duplicate_image_path = os.path.join(image_directory, duplicate_file)
                        duplicate_image_size = os.path.getsize(duplicate_image_path)
                        if duplicate_image_size > highest_image_size:
                            highest_image_size = duplicate_image_size
                            try:
                                os.remove(highest_image_path)
                            except FileNotFoundError:
                                pass
                            highest_image_path = duplicate_image_path
                            print(f'Deleted {highest_image_path}')
                        else:
                            try:
                                os.remove(duplicate_image_path)
                            except FileNotFoundError:
                                pass
                            print(f'Deleted {duplicate_image_path}')
            else:
                image_hash_dict.update({image_hash: filename})

directory = r'D:\Downloads\New Product'
similar_image(directory)