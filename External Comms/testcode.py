from timeit import default_timer as timer
import time

start = timer()
print("hello")
time.sleep(5)
end = timer()
print(start)
print(end)