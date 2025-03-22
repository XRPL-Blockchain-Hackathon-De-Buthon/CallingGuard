import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv1D, GlobalAveragePooling1D, LSTM, Reshape, Flatten
from sklearn.model_selection import train_test_split

# 데이터 로드
X = np.load("X.npy")  # (샘플 수, 특징 벡터 크기)
y = np.load("y.npy")

# 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# LSTM 입력 차원 변경
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)  # (샘플 수, 특징 벡터 크기, 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# CNN + LSTM 하이브리드 모델 정의
model = Sequential([
    Conv1D(64, kernel_size=3, activation='relu', input_shape=(X_train.shape[1], 1)),  # CNN 특징 추출
    GlobalAveragePooling1D(),
    
    Reshape((1, 64)),  # LSTM 입력 차원 맞추기 (필요시 수정)
    LSTM(64, return_sequences=True),  # 시계열 정보 학습
    Flatten(),
    
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')  # 보이스 피싱 여부 예측 (0=정상, 1=사기)
])

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# 모델 학습
model.fit(X_train, y_train, epochs=30, batch_size=16, validation_data=(X_test, y_test))

# 모델 저장
model.save("voice_phishing_model_v2.keras")
print("향상된 모델 학습 완료 & 저장됨!")
