""" GRADIO DEPLOY - VOICE PREDICTION """

from google.colab import drive
drive.mount('/content/drive')

""" PACKAGES """
!pip install gradio

!pip install python_speech_features

""" LIBRARIES """
from python_speech_features import mfcc
import scipy.io.wavfile as wav
import numpy as np
from tempfile import TemporaryFile
import os
import pickle
import random
import operator
import math
from collections import defaultdict
import gradio as gr


def getNeighbors(trainingSet , instance , k):
    distances =[]
    for x in range (len(trainingSet)):
        dist = distance(trainingSet[x], instance, k )+ distance(instance, trainingSet[x], k)
        distances.append((trainingSet[x][2], dist))
    distances.sort(key=operator.itemgetter(1))
    neighbors = []
    for x in range(k):
        neighbors.append(distances[x][0])
    return neighbors

def nearestClass(neighbors):
    classVote ={}
    for x in range(len(neighbors)):
        response = neighbors[x]
        if response in classVote:
            classVote[response]+=1
        else:
            classVote[response]=1
    sorter = sorted(classVote.items(), key = operator.itemgetter(1), reverse=True)
    return sorter[0][0]

def distance(instance1 , instance2 , k ):
    distance =0
    mm1 = instance1[0]
    cm1 = instance1[1]
    mm2 = instance2[0]
    cm2 = instance2[1]
    distance = np.trace(np.dot(np.linalg.inv(cm2), cm1))
    distance+=(np.dot(np.dot((mm2-mm1).transpose() , np.linalg.inv(cm2)) , mm2-mm1 ))
    distance+= np.log(np.linalg.det(cm2)) - np.log(np.linalg.det(cm1))
    distance-= k
    return distance

dataset = []
def loadDataset(filename , split , trSet , teSet):
    with open(f'/content/drive/MyDrive/test/extract_feature.dat' , 'rb') as f:
        while True:
            try:
                dataset.append(pickle.load(f))
            except EOFError:
                f.close()
                break

    for x in range(len(dataset)):
        if random.random() <split :
            trSet.append(dataset[x])
        else:
            teSet.append(dataset[x])

trainSet = []
testSet = []
loadDataset(f'/content/drive/MyDrive/test/extract_feature.dat' , 0.70, trainSet, testSet)

leng = len(testSet)
predict = []
for x in range (leng):
    predict.append(nearestClass(getNeighbors(trainSet ,testSet[x] , 5)))


""" GRADIO DEPLOYMENT """
def process_audio(audio):

    #Prediction for new data
    results=defaultdict(int)
    i=1
    for folder in os.listdir( f'/content/drive/MyDrive/cluster'):
        results[i]=folder
        i+=1
    #print(results)
    (rate,sig)=wav.read(audio)
    mfcc_feat=mfcc(sig,rate,winlen=0.020,appendEnergy=False)
    covariance = np.cov(np.matrix.transpose(mfcc_feat))
    mean_matrix = mfcc_feat.mean(0)
    feature=(mean_matrix,covariance,0)

    pred=nearestClass(getNeighbors(dataset ,feature , 5))

    return results[pred]

inputs = gr.inputs.Audio(type='filepath')
output = gr.outputs.Textbox()

gr.Interface(fn=process_audio, inputs=inputs, outputs=output).launch(share=True, debug=True)

