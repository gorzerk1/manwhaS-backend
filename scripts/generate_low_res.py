import os
from PIL import Image, ImageFilter
from tqdm import tqdm

source_root = "/home/ubuntu/backend/pictures"
target_root = "/home/ubuntu/backend/picturesLow"

TEMP_RESIZE_WIDTH = 50
BLUR_RADIUS = 1.5
FINAL_QUALITY = 10

def process_image(source_path, target_path):
    try:
        with Image.open(source_path) as img:
            original_size = img.size
            aspect_ratio = img.height / img.width
            temp_height = int(TEMP_RESIZE_WIDTH * aspect_ratio)

            # Step 1: shrink
            img = img.resize((TEMP_RESIZE_WIDTH, temp_height), Image.LANCZOS)

            # Step 2: scale back up
            img = img.resize(original_size, Image.NEAREST)

            # Step 3: blur
            img = img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

            # Step 4: save low-quality image
            img.save(target_path, quality=FINAL_QUALITY, optimize=True)

    except Exception as e:
        print(f"\n❌ Error processing {source_path}: {e}")

def walk_and_process():
    all_images = []

    # Collect all image paths
    for root, dirs, files in os.walk(source_root):
        relative_path = os.path.relpath(root, source_root)
        target_dir = os.path.join(target_root, relative_path)
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            if file.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_dir, file)

                # ✅ Skip if already exists
                if not os.path.exists(target_file):
                    all_images.append((source_file, target_file))

    print(f"🔍 Found {len(all_images)} new images to process...")

    for source_file, target_file in tqdm(all_images, desc="Processing images", unit="img"):
        process_image(source_file, target_file)

if __name__ == "__main__":
    print(f"📁 Starting from: {source_root}")
    walk_and_process()
    print("✅ Done! Blurry images saved to picturesLow.")
