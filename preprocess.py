import librosa
import numpy as np
import os

DATA_PATH = "data/"

def extract_audio_features(file_path):
    y, sr = librosa.load(file_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    return np.mean(mfcc.T, axis=0)

X = []
y = []
for filename in os.listdir(DATA_PATH):
    label = 1 if "phishing" in filename else 0
    X.append(extract_audio_features(os.path.join(DATA_PATH, filename)))
    y.append(label)

X = np.array(X)
y = np.array(y)
np.save("X.npy", X)
np.save("y.npy", y)
print(f"데이터셋 저장 완료: {X.shape}, 레이블 개수: {len(y)}")
