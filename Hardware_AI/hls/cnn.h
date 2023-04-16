#ifndef CNN
#define CNN
#define DATA_DEPTH 6
#define WINDOW_SIZE 45

#define KERNEL_SIZE 15
#define STRIDE 1
#define FILTER_SIZE 64

#define CNN_DEPTH FILTER_SIZE
#define CNN_OUTPUT_LENGTH ((WINDOW_SIZE - KERNEL_SIZE) / STRIDE + 1)
#define DENSE_INPUT CNN_DEPTH
#define DENSE_OUTPUT 5
typedef float float_num_t;
typedef int RESET_BIT;

void cnn_buffer(
		RESET_BIT reset,
		int user,
		float data[DATA_DEPTH],
		float output[DENSE_OUTPUT]);

void run_cnn_layer(
        float_num_t cnn_input_buffer[KERNEL_SIZE][DATA_DEPTH],
        float_num_t cnn_weights[FILTER_SIZE][KERNEL_SIZE][DATA_DEPTH],
        float_num_t cnn_biases[FILTER_SIZE],
        float_num_t cnn_output_buffer[CNN_OUTPUT_LENGTH][CNN_DEPTH],
        float_num_t global_average[CNN_DEPTH]
);

void run_dense_layer(
        float_num_t input_buffer[CNN_DEPTH],
        float_num_t dense_weights[DENSE_OUTPUT][DENSE_INPUT],
        float_num_t dense_bias[DENSE_OUTPUT],
        float_num_t dense_output[DENSE_OUTPUT]
);

template<typename T>
T argmax(T input[]){
    float_num_t max = input[0];
    int idx = 0;
    ARGMAX: for (int i = 1; i < DENSE_OUTPUT; i++) {
    if (input[i] > max) {
        max = input[i];
        idx = i;
    }
}
    return idx;
}

#endif
