import os
import tensorflow as tf
from tensorflow.keras.layers import Input
from tensorflow.keras.utils import multi_gpu_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, CSVLogger, TerminateOnNaN
import tensorflow.keras.backend as K
from hyperparameters import *
from losses import *
from network import network
from datagenerator import DataGenerator
from modelmemory import memory_usage

################################################################################
# Compiling
################################################################################

input_img = Input(input_dimensions)
with tf.device('/cpu:0'):
    model = network(input_img,
                    n_filters=num_initial_filters,
                    batchnorm=batchnorm)

if num_gpu > 1:
    parallel_model = multi_gpu_model(model, gpus=num_gpu, cpu_merge=False)
    parallel_model.compile(optimizer=Adam(lr=learning_rate),
                           loss=loss,
                           metrics=metrics)
else:
    model.compile(optimizer=Adam(lr=learning_rate), loss=loss, metrics=metrics)

callbacks = [
    EarlyStopping(monitor='', patience=400, verbose=1),
    ReduceLROnPlateau(factor=0.1,
                      monitor='',
                      patience=50,
                      min_lr=0.00001,
                      verbose=1,
                      mode='max'),
    ModelCheckpoint(checkpoint_path,
                    monitor='',
                    mode='max',
                    verbose=0,
                    save_best_only=True),
    CSVLogger(log_path, separator=',', append=True),
    TerminateOnNaN()
]

# Prints a rough estimation of the GPU memory per GPU required to store the model
print('Memory Footprint/GPU: ' + str(memory_usage(1, model)) + 'GB')

################################################################################
# Training
################################################################################

list_IDs = []
for filename in os.listdir(train_path):
    # Write logic to add filenames of train images to list_IDs which will be processed by DataGenerator
    # later on
    pass

train_gen = DataGenerator(list_IDs=list_IDs,
                          dim=dimensions,
                          batch_size=batch_size,
                          shuffle=True)

if num_gpu > 1:
    parallel_model.fit_generator(train_gen,
                                 steps_per_epoch=steps_per_epoch,
                                 epochs=epochs,
                                 verbose=2,
                                 callbacks=callbacks,
                                 workers=20)
else:
    model.fit_generator(train_gen,
                        steps_per_epoch=steps_per_epoch,
                        epochs=epochs,
                        verbose=2,
                        callbacks=callbacks,
                        workers=20)

model.save(save_path)
