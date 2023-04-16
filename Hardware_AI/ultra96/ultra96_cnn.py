from pynq import Overlay
import numpy as np
from time import time
import pynq


def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


# class_labels = ["LOGOUT", "GRENADE", "RELOAD", "SHIELD"]
class_labels = ['WALKING', 'GRENADE', 'RELOAD', 'SHIELD', 'LOGOUT']


def set_up_fpga():
    print("Uploading bitstream to FPGA...")
    # overlay = Overlay("cnnlast9.bit")
    overlay = Overlay("cnnlast12.bit")
    cnn = overlay.cnn_buffer_0
    cnn.input = pynq.allocate(shape=(6,), dtype=np.float32)
    cnn.register_map.data = cnn.input.device_address
    # print(cnn.register_map)
    cnn.outputs = pynq.allocate(shape=(5,), dtype=np.float32)
    cnn.register_map.raw_output = cnn.outputs.device_address
    print("Bitstream Uploaded")
    return cnn


def reset_model(cnn, user):
    cnn.register_map.reset = 1
    cnn.register_map.user = user
    cnn.register_map.CTRL.AP_START = 1
    while (cnn.register_map.CTRL.AP_DONE == 0): pass


def run_inference(cnn, data, user):
    # threshold = 0.84
    threshold = 0.815
    # threshold = 0.93
    cnn.input[:] = np.float32([k / 4096.0 for k in data])
    # print("Inferencing results...")
    cnn.register_map.reset = 0
    cnn.register_map.user = user
    cnn.register_map.CTRL.AP_START = 1
    while (cnn.register_map.CTRL.AP_DONE == 0): pass
    predicted_class = np.argmax(cnn.outputs)
    confidence = max(softmax(cnn.outputs))
    if confidence < threshold:
        # print("Action below threshold")
        predicted_class = -1
    return predicted_class


def test_FPGA(cnn, user):
    data = np.float32(np.load("test_x.npy"))
    labels = np.load("test_y.npy")
    # data = np.float32(np.load("test_x_free_player.npy"))
    # labels = np.load("test_y_free_player.npy")
    threshold = 0.815
    shield_fp_count = 0
    grenade_fp_count = 0
    shield_softmax = 0
    reload_softmax = 0
    reload_softmax_pure = 0
    reload_softmax_pure_count = 0
    grenade_softmax = 0
    logout_softmax = 0
    inference_count = 0
    threshold_miss_count = 0
    confusion_matrix = np.zeros((5, 5))
    start_time = time()
    correct_count = 0
    total_count = 0
    for i in range(0, data.shape[0]):
        actual = np.argmax(labels[i])
        pass_thresh = False

        for j in range(0, data.shape[1]):
            data_cols = data[i, j, :]
            cnn.input[:] = [k for k in data_cols]

            cnn.register_map.reset = 0
            cnn.register_map.user = user
            cnn.register_map.CTRL.AP_START = 1
            while (cnn.register_map.CTRL.AP_DONE == 0): pass

            predicted_class = np.argmax(cnn.outputs)
            confidence = max(softmax(cnn.outputs))
            if confidence < threshold:
                predicted_class = -1

            predicted = predicted_class
            inference_count += 1
            if predicted != -1:
                pass_thresh = True
                break
        softmax_results = softmax(cnn.outputs)
        if pass_thresh:
            if predicted == actual:
                correct_count += 1
            elif predicted == 4 and actual == 1:
                grenade_softmax += softmax_results[1]
                logout_softmax += softmax_results[4]
                grenade_fp_count += 1
            else:
                threshold_miss_count += 1
            confusion_matrix[actual, predicted] += 1

            cnn.register_map.reset = 1
            cnn.register_map.user = user
            cnn.register_map.CTRL.AP_START = 1
            while (cnn.register_map.CTRL.AP_DONE == 0): pass

    print(f"Average time for one inference= {(time() - start_time) / inference_count}")
    print(f"Threshold miss rate = {threshold_miss_count / data.shape[0]}")
    # print(f"Accuracy = {correct_count / data.shape[0]}")
    # print(f"Average shield softmax = {shield_softmax/shield_fp_count}")
    # print(f"Average reload softmax pure = {reload_softmax_pure/reload_softmax_pure_count}")
    # print(f"Average reload softmax = {reload_softmax/shield_fp_count}")
    # print(f"Average grenade softmax = {grenade_softmax/grenade_fp_count}")
    print(confusion_matrix)

# cnn = set_up_fpga()
# test_FPGA(cnn, 0)
