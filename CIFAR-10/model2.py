import os
import numpy as np
import keras as keras
from keras.models import Model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, ReduceLROnPlateau
from keras.layers import Input, MaxPool2D, Activation, BatchNormalization, UpSampling2D, concatenate, LeakyReLU
from dataset import load_data

EPOCHS = 500
BATCH_SIZE = 128
LEARNING_RATE = 0.002
INPUT_SHAPE = (32, 32, 1)
WEIGHTS = 'model2.hdf5'

data = load_data()
np.random.shuffle(data)
Y_channel = data[:, 0, :].reshape(50000, 32, 32, 1)
UV_channel = data[:, 1:, :].reshape(50000, 32, 32, 2)


def Conv2D(filters, kernel_size, inputs, name=None, padding='same', activation='relu'):
    conv = keras.layers.Conv2D(filters, kernel_size, padding=padding, kernel_initializer='he_normal', name=name)(inputs)
    conv = BatchNormalization()(conv)

    if activation == 'relu':
        conv = Activation(activation)(conv)
    elif activation == 'leakyrelu':
        conv = LeakyReLU()(conv)

    return conv


def create_model():
    inputs = Input(INPUT_SHAPE)
    conv1 = Conv2D(64, (3, 3), inputs, 'conv1_1', activation='leakyrelu')
    conv1 = Conv2D(64, (3, 3), conv1, 'conv1_2', activation='leakyrelu')
    pool1 = MaxPool2D((2, 2))(conv1)

    conv2 = Conv2D(128, (3, 3), pool1, 'conv2_1', activation='leakyrelu')
    conv2 = Conv2D(128, (3, 3), conv2, 'conv2_2', activation='leakyrelu')
    pool2 = MaxPool2D((2, 2))(conv2)

    conv3 = Conv2D(256, (3, 3), pool2, 'conv3_1', activation='leakyrelu')
    conv3 = Conv2D(256, (3, 3), conv3, 'conv3_2', activation='leakyrelu')
    pool3 = MaxPool2D((2, 2))(conv3)

    conv4 = Conv2D(512, (3, 3), pool3, 'conv4_1', activation='leakyrelu')
    conv4 = Conv2D(512, (3, 3), conv4, 'conv4_2', activation='leakyrelu')
    pool4 = MaxPool2D((2, 2))(conv4)

    conv5 = Conv2D(1024, (3, 3), pool4, 'conv5_1', activation='leakyrelu')
    conv5 = Conv2D(1024, (3, 3), conv5, 'conv5_2', activation='leakyrelu')

    up6 = Conv2D(512, (2, 2), UpSampling2D((2, 2))(conv5), 'up6', activation='relu')
    merge6 = concatenate([conv4, up6], axis=3)
    conv6 = Conv2D(512, (3, 3), merge6, 'conv6_1', activation='relu')
    conv6 = Conv2D(512, (3, 3), conv6, 'conv6_2', activation='relu')

    up7 = Conv2D(256, (2, 2), UpSampling2D((2, 2))(conv6), 'up7', activation='relu')
    merge7 = concatenate([conv3, up7], axis=3)
    conv7 = Conv2D(256, (3, 3), merge7, 'conv7_1', activation='relu')
    conv7 = Conv2D(256, (3, 3), conv7, 'conv7_2', activation='relu')

    up8 = Conv2D(128, (2, 2), UpSampling2D((2, 2))(conv7), 'up8', activation='relu')
    merge8 = concatenate([conv2, up8], axis=3)
    conv8 = Conv2D(128, (3, 3), merge8, 'conv8_1', activation='relu')
    conv8 = Conv2D(128, (3, 3), conv8, 'conv8_2', activation='relu')

    up9 = Conv2D(64, (2, 2), UpSampling2D((2, 2))(conv8))
    merge9 = concatenate([conv1, up9], axis=3)
    conv9 = Conv2D(64, (3, 3), merge9, 'conv9_1', activation='relu')
    conv9 = Conv2D(64, (3, 3), conv9, 'conv9_2', activation='relu')
    conv9 = keras.layers.Conv2D(2, (1, 1), padding='same', name='conv9_3')(conv9)

    model = Model(inputs=inputs, outputs=conv9)
    model.compile(optimizer=Adam(LEARNING_RATE),
                  loss='mean_squared_error',
                  metrics=['accuracy'])

    return model


model = create_model()
model_checkpoint = ModelCheckpoint(
    filepath=WEIGHTS,
    monitor='loss',
    verbose=1,
    save_best_only=True)

reduce_lr = ReduceLROnPlateau(
    monitor='loss',
    factor=0.5,
    patience=20)

if os.path.exists(WEIGHTS):
    model.load_weights(WEIGHTS)

model.fit(
    Y_channel,
    UV_channel,
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
    verbose=1,
    validation_split=0.1,
    callbacks=[model_checkpoint, reduce_lr])
