import tensorflow as tf

print("TensorFlow version:", tf.__version__)
print("Keras version:", tf.keras.__version__)

# Simple test
a = tf.constant([2, 3])
b = tf.constant([4, 5])
print("TensorFlow test:", tf.add(a, b))
