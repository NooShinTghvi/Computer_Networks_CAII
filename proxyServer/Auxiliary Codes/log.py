import logging
import threading
import time

def worker(arg):
    while not arg['stop']:
        logging.debug('debug message _ worker')
        logging.info('info message _ worker')
        logging.warning('warn message _ worker')
        logging.error('error message _ worker')
        logging.critical('critical message _ worker')
        time.sleep(0.5)

def main():
    #%(relativeCreated)6d
    #%(threadName)s
    LogFile=logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)-21s %(levelname)-8s %(message)s',
        datefmt='[%y/%m/%d %H:%M:%S]:',
        filename='myapp.log',
        filemode = 'w'
    )
    info = {'stop': False}
    thread = threading.Thread(target=worker, args=(info,))
    thread.start()
    while True:
        try:
            logging.debug('debug message')
            logging.info('info message')
            logging.warning('warn message')
            logging.error('error message')
            logging.critical('critical message')
            time.sleep(1)
        except KeyboardInterrupt:
            info['stop'] = True
            break
    thread.join()

if __name__ == '__main__':
    main()