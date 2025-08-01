#!/usr/bin/env python3
"""
Скрипт для запуска нескольких ML воркеров
"""

import os
import sys
import time
import subprocess
import signal
from concurrent.futures import ThreadPoolExecutor
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerManager:
    """Менеджер для управления несколькими воркерами"""
    
    def __init__(self, num_workers: int = 3):
        self.num_workers = num_workers
        self.processes = []
        self.running = True
        
        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Получен сигнал {signum}. Завершение работы всех воркеров")
        self.running = False
        self.stop_all_workers()
    
    def start_worker(self, worker_id: str) -> subprocess.Popen:
        """Запуск одного воркера"""
        try:
            cmd = [sys.executable, "worker.py", "--worker-id", worker_id]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info(f"Воркер {worker_id} запущен (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"Ошибка запуска воркера {worker_id}: {e}")
            raise
    
    def monitor_worker(self, process: subprocess.Popen, worker_id: str) -> None:
        """Мониторинг воркера и вывод логов"""
        try:
            for line in process.stdout:
                if line.strip():
                    print(f"[{worker_id}] {line.strip()}")
                
                if not self.running:
                    break
                    
            process.wait()
            
            if self.running:
                logger.warning(f"Воркер {worker_id} завершился неожиданно")
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга воркера {worker_id}: {e}")
    
    def start_all_workers(self) -> None:
        """Запуск всех воркеров"""
        logger.info(f"Запуск {self.num_workers} воркеров")
        
        try:
            # Запуск процессов воркеров
            for i in range(self.num_workers):
                worker_id = f"worker-{i+1}"
                process = self.start_worker(worker_id)
                self.processes.append((process, worker_id))
            
            # Мониторинг воркеров в отдельных потоках
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = []
                
                for process, worker_id in self.processes:
                    future = executor.submit(self.monitor_worker, process, worker_id)
                    futures.append(future)
                
                # Ожидание завершения всех воркеров
                for future in futures:
                    future.result()
                    
        except Exception as e:
            logger.error(f"Ошибка при запуске воркеров: {e}")
            self.stop_all_workers()
            raise
    
    def stop_all_workers(self) -> None:
        """Остановка всех воркеров"""
        logger.info("Остановка всех воркеров")
        
        for process, worker_id in self.processes:
            try:
                if process.poll() is None:  # Процесс еще работает
                    logger.info(f"Отправка SIGTERM воркеру {worker_id}")
                    process.terminate()
                    
                    # Ждем 10 секунд на graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"Воркер {worker_id} завершен успешно")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Принудительное завершение воркера {worker_id}")
                        process.kill()
                        process.wait()
                        
            except Exception as e:
                logger.error(f"Ошибка остановки воркера {worker_id}: {e}")
        
        self.processes.clear()
    
    def run(self) -> None:
        """Основной цикл работы менеджера"""
        try:
            self.start_all_workers()
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        finally:
            self.stop_all_workers()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Менеджер ML воркеров')
    parser.add_argument(
        '--workers', 
        type=int, 
        default=3, 
        help='Количество воркеров для запуска (по умолчанию: 3)'
    )
    
    args = parser.parse_args()
    
    if args.workers < 1:
        logger.error("Количество воркеров должно быть больше 0")
        sys.exit(1)
    
    logger.info(f"Запуск менеджера воркеров с {args.workers} воркерами")
    
    manager = WorkerManager(args.workers)
    manager.run()


if __name__ == "__main__":
    main()