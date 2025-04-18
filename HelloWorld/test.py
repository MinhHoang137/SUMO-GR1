import numpy as np
import matplotlib.pyplot as plt

# Mã lệnh gửi (0x00FF40BF) -> dạng nhị phân 34 bit (gồm bit khởi đầu, bit cuối và dữ liệu)
data = '0' + '00000000111111110100000010111111' + '0'

# Thông số thời gian (đơn vị: microsecond)
START_PULSE = 9000   # xung khởi đầu (9ms)
START_GAP = 4500     # khoảng nghỉ sau xung khởi đầu (4.5ms)
BIT_HIGH_PULSE = 560 # xung cho bit 1 hoặc bit 0 (0.56ms)
BIT_1_GAP = 1690     # khoảng nghỉ cho bit 1 (1.69ms)
BIT_0_GAP = 560      # khoảng nghỉ cho bit 0 (0.56ms)
END_PULSE = 560      # xung kết thúc (0.56ms)

# Xây dựng dữ liệu tín hiệu
signal = []
time = []

# Thêm xung khởi đầu
signal += [1] * int(START_PULSE / 10)
time += list(np.linspace(0, START_PULSE, int(START_PULSE / 10)))

signal += [0] * int(START_GAP / 10)
time += list(np.linspace(START_PULSE, START_PULSE + START_GAP, int(START_GAP / 10)))

# Thêm các bit dữ liệu
current_time = START_PULSE + START_GAP
for bit in data:
    # Thêm xung bắt đầu cho bit
    signal += [1] * int(BIT_HIGH_PULSE / 10)
    time += list(np.linspace(current_time, current_time + BIT_HIGH_PULSE, int(BIT_HIGH_PULSE / 10)))
    current_time += BIT_HIGH_PULSE

    # Thêm khoảng nghỉ cho bit
    if bit == '1':
        signal += [0] * int(BIT_1_GAP / 10)
        time += list(np.linspace(current_time, current_time + BIT_1_GAP, int(BIT_1_GAP / 10)))
        current_time += BIT_1_GAP
    else:
        signal += [0] * int(BIT_0_GAP / 10)
        time += list(np.linspace(current_time, current_time + BIT_0_GAP, int(BIT_0_GAP / 10)))
        current_time += BIT_0_GAP

# Thêm xung kết thúc
signal += [1] * int(END_PULSE / 10)
time += list(np.linspace(current_time, current_time + END_PULSE, int(END_PULSE / 10)))
current_time += END_PULSE

# Đảo ngược tín hiệu đầu ra theo nguyên lý hoạt động của HS0038
inverted_signal = [1 - s for s in signal]

# Vẽ biểu đồ
plt.figure(figsize=(16, 6))
plt.step(time, inverted_signal, where='post', label='Tín hiệu đầu ra ')

# Ghi chú từng bit
bit_duration = BIT_HIGH_PULSE + BIT_1_GAP
current_time = START_PULSE + START_GAP + bit_duration / 2
for i, bit in enumerate(data):
    plt.text(current_time, 0.8, bit, ha='center', va= 'center', fontsize=10)
    current_time += BIT_HIGH_PULSE + (BIT_1_GAP if bit == '1' else BIT_0_GAP)

# Định dạng biểu đồ
plt.ylim(-0.2, 1.5)
plt.xlim(0, current_time + END_PULSE)
plt.xlabel('Thời gian (microsecond)')
plt.ylabel('Mức logic')
plt.title('Tín hiệu đầu ra của cảm biến hồng ngoại HS0038 (0x00FF40BF)')
plt.legend()
plt.grid(True)

# Hiển thị biểu đồ
plt.show()

