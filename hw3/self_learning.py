import sys
import pandas as pd
import numpy as np
from keras.models import Sequential, load_model
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import Adam
from keras.utils import np_utils
from keras.preprocessing.image import ImageDataGenerator
from keras.layers.normalization import BatchNormalization
from keras import backend as K

#parameter
batch_size = 128
num_classes = 7
epochs = 50
iteration = 10
bound = 0.9
data_augmentation = True

#image dim
img_rows = 48
img_cols = 48

#sys.argv
train = sys.argv[1]
test = sys.argv[2]
name_model = sys.argv[3]

#read train data
#training label
traindata = pd.read_csv(train)
y_train = traindata.label
y_train = np.array(y_train)
y_train = np_utils.to_categorical(y_train, num_classes)
#training feature
x_train = traindata.feature.str.split(' ')
x_train = x_train.tolist()
x_train = np.array(x_train)
x_train = x_train.astype('float32')
x_train /= 255
x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)

#read test data (unlabel data)
testdata = pd.read_csv(test)
x_test = testdata.feature.str.split(' ')
x_test = x_test.tolist()
x_test = np.array(x_test)
x_test = x_test.astype('float32')
x_test /= 255
x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)

#CNN model
model = Sequential()

model.add(Convolution2D(32,3,3,input_shape=(img_rows,img_cols,1)))
model.add(Activation('relu'))

model.add(Convolution2D(32,3,3))
model.add(Activation('relu'))

model.add(Convolution2D(32,3,3))
model.add(Activation('relu'))
model.add(MaxPooling2D(2,2))
model.add(Dropout(0.25))

model.add(Convolution2D(64,3,3))
model.add(Activation('relu'))

model.add(Convolution2D(64,3,3))
model.add(Activation('relu'))

model.add(Convolution2D(64,3,3))
model.add(Activation('relu'))
model.add(MaxPooling2D(2,2))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Dropout(0.25))
model.add(Dense(256))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Dropout(0.25))
model.add(Dense(128))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(Dropout(0.25))
model.add(Dense(num_classes))
model.add(BatchNormalization())
model.add(Activation('softmax'))
model.summary()

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

#augmentation for training data
if data_augmentation == True:
    print("data augmentation")
    datagen = ImageDataGenerator(
            featurewise_center=False,  # set input mean to 0 over the dataset
            samplewise_center=False,  # set each sample mean to 0
            featurewise_std_normalization=False,  # divide inputs by std of the dataset
            samplewise_std_normalization=False,  # devide each input by its std
            zca_whitening=False,  # apply ZCA whitening
            rotation_range=8,  # randomly rotate images in range
            width_shift_range=0.1,  # randomly shift images horizontally
            height_shift_range=0.1,  # randomly shift images vertically
            horizontal_flip=True,  # randomly flip images
            vertical_flip=False)  # randomly flip images
else:
    print("No data augmentation")

#for self learning
for i in range(iteration):
    if data_augmentation == True:
        datagen.fit(x_train)    
        model.fit_generator(datagen.flow(x_train, y_train, batch_size=batch_size),
					       steps_per_epoch=(x_train.shape[0]//batch_size), 
					       epochs=epochs)
    else:
        model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs)
        
    pre_label = model.predict(x_test)
    tmp_data = []
    tmp_label = []
    delete_index = []
    for j in range(len(pre_label)):
        for k in range(7):
            if pre_label[j][k] > bound:
                tmp_data.append(x_test[j])
                tmp_label.append(k)
                delete_index.append(j)
    tmp_data = np.array(tmp_data)
    tmp_label = np.array(tmp_label)
    delete_index = np.array(delete_index)
    tmp_label = np_utils.to_categorical(tmp_label, num_classes)
    x_train = np.concatenate((x_train, tmp_data), axis=0)
    y_train = np.concatenate((y_train, tmp_label), axis=0)
    x_test = np.delete(x_test, delete_index, axis=0)
    print(x_train.shape)
    print(y_train.shape)
    print(x_test.shape)

#save model
model.save(name_model)