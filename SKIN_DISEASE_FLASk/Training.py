import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Flatten, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Sequential, Model


# NEW CLASSES
DISEASE_CLASSES = [
    'Acne',
    'Lentigines',
    'Leprosy',
    'Melasma',
    'Other',
    'Periorbital_hyperpigmentation',
    'Postinflammatory_hyperpigmentation',
    'Vitiligo'
]

IMG_SIZE = 224
BATCH_SIZE = 16
NUM_CLASSES = 8


def total_files(folder_path):
    """Count number of image files in a folder."""
    if not os.path.exists(folder_path):
        return 0
    return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])


def analyze_dataset():
    """Analyze dataset structure"""
    print("\n========== DATASET SUMMARY ==========\n")

    base_dirs = {
        "Train": "Dataset/Train",
        "Test": "Dataset/Test",
        "Validation": "Dataset/Validation"
    }

    for dataset_name, base_path in base_dirs.items():
        print(f"\n--- {dataset_name} Dataset ---")
        for cls in DISEASE_CLASSES:
            folder = os.path.join(base_path, cls)
            print(f"{cls:35s}: {total_files(folder)} images")


def create_model():
    """Transfer Learning Model using MobileNetV2"""

    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )

    base_model.trainable = False  # Freeze base model

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(128, activation='relu')(x)
    output = Dense(NUM_CLASSES, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=output)

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    return model


def train_model():
    """Train the model"""

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True
    )

    test_datagen = ImageDataGenerator(rescale=1.0 / 255)

    train_generator = train_datagen.flow_from_directory(
        'Dataset/Train',
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )

    validation_generator = test_datagen.flow_from_directory(
        'Dataset/Validation',
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )

    model = create_model()
    print("\nModel Summary:")
    model.summary()

    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // train_generator.batch_size,
        epochs=20,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // validation_generator.batch_size
    )

    model.save("skin_disease_model.h5")
    print("\nModel saved as 'skin_disease_model.h5'")

    np.save("class_indices.npy", train_generator.class_indices)
    print("Class indices saved as class_indices.npy")

    plot_training_history(history)

    return model, history, train_generator


def plot_training_history(history):
    """Plot accuracy & loss graphs"""
    sns.set_theme()
    sns.set_context("poster")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    ax1.plot(history.history['accuracy'], label='Training Accuracy', linewidth=3)
    ax1.plot(history.history['val_accuracy'], label='Validation Accuracy', linewidth=3)
    ax1.set_title('Model Accuracy', fontsize=16)
    ax1.set_xlabel('Epoch', fontsize=14)
    ax1.set_ylabel('Accuracy', fontsize=14)
    ax1.legend(fontsize=12)
    ax1.grid(True)

    ax2.plot(history.history['loss'], label='Training Loss', linewidth=3)
    ax2.plot(history.history['val_loss'], label='Validation Loss', linewidth=3)
    ax2.set_title('Model Loss', fontsize=16)
    ax2.set_xlabel('Epoch', fontsize=14)
    ax2.set_ylabel('Loss', fontsize=14)
    ax2.legend(fontsize=12)
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("training_history.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    analyze_dataset()
    print("\nStarting model training for 8 classes...")
    model, history, train_generator = train_model()
