from model_proxy import JointNet
import keras	
import numpy as np
from keras.utils import plot_model
import os
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from keras.callbacks import ModelCheckpoint
import timeit
import json
import pandas as pd


if __name__ == '__main__':

    start = timeit.default_timer()
    BATCH_SIZE = 32
    train_path = ''
    val_path = ''

    with open(train_path+'/data_kmeans_train.pkl', 'rb') as fp:
        img_data_train = pickle.load(fp)

    with open(val_path+'/data_kmeans_val.pkl', 'rb') as fp:
        img_data_val = pickle.load(fp)
        
    classes = list(img_data_train.keys())
    label_ind = {c:i for i,c in enumerate(classes)}    
    
    ip_size = img_data_train[classes[0]][0].shape[0]
    jointnet = JointNet(ip_size)
    model = jointnet.model
    # plot_model(model, 'proxymodel.png')
    # input()

    df_train = pd.read_csv(train_path+'/train_data_proxy.csv')
    df_val = pd.read_csv(val_path+'val_data_proxy.csv')
   

    def generator(df, img_data):
        
        num_samples = df.shape[0]
        i = 0
        while True:

            if i%num_samples==0:
                df = df.sample(frac=1).reset_index(drop=True)                
                i = 0
                
        
            anchor_labels = df['0'].values[i:i+BATCH_SIZE]
            anchor_indices = df['1'].values[i:i+BATCH_SIZE]
            
            
            anchor_img = []
            class_mask = np.zeros((BATCH_SIZE, 576))
            class_mask_bar = np.ones((BATCH_SIZE, 576))
            for s in range(BATCH_SIZE):                
                label = anchor_labels[s]
                class_mask[s][label_ind[label]] = 1
                class_mask_bar[s][label_ind[label]] = 0
        
                anchor_img.append(img_data[label][anchor_indices[s]])
                  
                               
            yield [np.array(anchor_img), np.array(class_mask), np.array(class_mask_bar)], np.zeros(BATCH_SIZE)
            
            i += BATCH_SIZE



    filepath = "proxy_loss_deep2_actual_newdata.keras"
    checkpoint = ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True, save_weights_only=True, mode='min', period=1)
    callbacks_list = [checkpoint]


    # NOTE: val set consists of seen images and unseen audio so we are repeating img_data_train for val generator

    num_train_batches = (df_train.shape[0] / BATCH_SIZE)
    num_val_batches = (df_val.shape[0] / BATCH_SIZE)
    history = model.fit_generator(generator(df_train, img_data_train), steps_per_epoch=num_train_batches, epochs=400, callbacks=callbacks_list, validation_data=generator(df_val, img_data_train), validation_steps=num_val_batches)


    print(history.history.keys())
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.legend(['train', 'val'], loc='upper left')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.savefig("proxy_loss_deep2_actual_newdata.png", bbox_inches = 'tight', pad_inches = 0)
    plt.close()

   
    with open('/history_proxy_loss_deep2_actual_newdata.json', 'w') as fp:
        json.dump(history.history, fp)

    stop = timeit.default_timer()
    time = open('time.txt','w')
    time.write(str(stop-start))
    
