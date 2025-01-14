import pytest
import threading

def thread_test(cv):
    print(f"{threading.current_thread().name} has started")
    for i in range(10000):
        if i % 1000 == 0:
            with cv:
                print(i)
                cv.notify()
    return 'thread done'

if __name__ == '__main__':
    cv = threading.Condition()
    t1 = threading.Thread(name='t1', target=thread_test, args=[cv])
    t1.start()
    t2 = threading.Thread(name='t2', target=thread_test, args=[cv])
    t2.start()
    t1.join()
    t2.join()