# -*- coding: utf-8 -*-
"""
温湿度环境监测系统 - 项目一实现
作者: [你的名字]
日期: 2024年[日期]
"""

import csv
import chardet
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from datetime import datetime
import logging
import sys
import os

# ==================== 类定义部分 ====================

class SensorDataReader:
    """传感器数据读取器类"""
    
    def __init__(self):
        self.clean_data = []
        self.raw_lines = []
        self.error_log = []
        
    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding']
        except Exception as e:
            print(f"文件编码检测失败: {e}")
            return 'utf-8'
    
    def read_csv(self, file_path):
        """读取CSV文件，自动检测编码，过滤异常数据"""
        encoding = self.detect_encoding(file_path)
        print(f"检测到文件编码: {encoding}")
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                csv_reader = csv.DictReader(f)
                self.raw_lines = list(csv_reader)
                
                for i, row in enumerate(self.raw_lines):
                    try:
                        # 尝试解析数据
                        timestamp = row.get('timestamp', '').strip()
                        temp_str = row.get('temperature', '').strip()
                        humid_str = row.get('humidity', '').strip()
                        
                        # 跳过空行或缺失数据
                        if not timestamp or not temp_str or not humid_str:
                            self._log_error(f"第{i+2}行: 数据缺失 - {row}")
                            continue
                        
                        # 尝试转换为数值
                        try:
                            temperature = float(temp_str)
                            humidity = float(humid_str)
                        except ValueError:
                            self._log_error(f"第{i+2}行: 数据格式错误 - {row}")
                            continue
                        
                        # 检查数据范围
                        temp_normal = 20 <= temperature <= 30
                        humid_normal = 40 <= humidity <= 60
                        
                        if temp_normal and humid_normal:
                            self.clean_data.append({
                                'timestamp': timestamp,
                                'temperature': temperature,
                                'humidity': humidity
                            })
                        else:
                            self._log_error(f"第{i+2}行: 数据超出范围 - 温度:{temperature}℃, 湿度:{humidity}%")
                            
                    except Exception as e:
                        self._log_error(f"第{i+2}行: 处理错误 - {e}")
            
            print(f"数据读取完成: 共{len(self.raw_lines)}行，有效数据{len(self.clean_data)}行")
            return self.clean_data
            
        except Exception as e:
            print(f"文件读取失败: {e}")
            return []
    
    def _log_error(self, error_msg):
        """记录错误日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {error_msg}"
        self.error_log.append(full_msg)
        print(full_msg)
    
    def save_error_log(self, file_path='error.log'):
        """保存错误日志到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for error in self.error_log:
                    f.write(error + '\n')
            print(f"错误日志已保存到: {file_path}")
        except Exception as e:
            print(f"保存错误日志失败: {e}")


class SensorData:
    """传感器数据基类"""
    
    def __init__(self, raw_data):
        self.__raw_data = raw_data  # 私有属性，保护原始数据
    
    def get_raw_data(self):
        """获取原始数据（只读）"""
        return self.__raw_data.copy()
    
    def get_clean_data(self):
        """获取清洗后的数据 - 需要在子类中实现具体逻辑"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_anomaly_count(self):
        """获取异常数据数量 - 需要在子类中重写"""
        raise NotImplementedError("子类必须实现此方法")


class TemperatureData(SensorData):
    """温度数据子类"""
    
    def __init__(self, raw_data):
        super().__init__(raw_data)
        self.temp_data = []
        self._process_data()
    
    def _process_data(self):
        """处理温度数据"""
        for row in self.get_raw_data():
            try:
                temp = float(row.get('temperature', 0))
                self.temp_data.append({
                    'timestamp': row.get('timestamp'),
                    'temperature': temp,
                    'is_anomaly': not (20 <= temp <= 30)
                })
            except (ValueError, TypeError):
                continue
    
    def get_clean_data(self):
        """获取清洗后的温度数据"""
        clean = [d for d in self.temp_data if not d['is_anomaly']]
        return clean
    
    def get_anomaly_count(self):
        """统计温度异常次数"""
        anomalies = [d for d in self.temp_data if d['is_anomaly']]
        return len(anomalies)
    
    def get_temperature_list(self):
        """获取温度列表"""
        return [d['temperature'] for d in self.temp_data]
    
    def get_timestamps(self):
        """获取时间戳列表"""
        return [d['timestamp'] for d in self.temp_data]
    
    def get_anomaly_points(self):
        """获取异常点数据"""
        return [d for d in self.temp_data if d['is_anomaly']]


class HumidityData(SensorData):
    """湿度数据子类"""
    
    def __init__(self, raw_data):
        super().__init__(raw_data)
        self.humid_data = []
        self._process_data()
    
    def _process_data(self):
        """处理湿度数据"""
        for row in self.get_raw_data():
            try:
                humid = float(row.get('humidity', 0))
                self.humid_data.append({
                    'timestamp': row.get('timestamp'),
                    'humidity': humid,
                    'is_anomaly': not (40 <= humid <= 60)
                })
            except (ValueError, TypeError):
                continue
    
    def get_clean_data(self):
        """获取清洗后的湿度数据"""
        clean = [d for d in self.humid_data if not d['is_anomaly']]
        return clean
    
    def get_anomaly_count(self):
        """统计湿度异常次数"""
        anomalies = [d for d in self.humid_data if d['is_anomaly']]
        return len(anomalies)
    
    def get_humidity_list(self):
        """获取湿度列表"""
        return [d['humidity'] for d in self.humid_data]
    
    def get_timestamps(self):
        """获取时间戳列表"""
        return [d['timestamp'] for d in self.humid_data]
    
    def get_anomaly_points(self):
        """获取异常点数据"""
        return [d for d in self.humid_data if d['is_anomaly']]


class DataAnalyzer:
    """数据分析器类"""
    
    def __init__(self, temp_data_obj, humid_data_obj):
        self.temp_data = temp_data_obj
        self.humid_data = humid_data_obj
    
    def calculate_hourly_average(self):
        """计算小时均值"""
        try:
            # 创建DataFrame以便分组
            temp_df = pd.DataFrame(self.temp_data.get_clean_data())
            humid_df = pd.DataFrame(self.humid_data.get_clean_data())
            
            if temp_df.empty or humid_df.empty:
                print("无有效数据用于计算小时均值")
                return {}, {}
            
            # 转换时间戳
            temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'])
            humid_df['timestamp'] = pd.to_datetime(humid_df['timestamp'])
            
            # 按小时分组计算均值
            temp_df['hour'] = temp_df['timestamp'].dt.hour
            humid_df['hour'] = humid_df['timestamp'].dt.hour
            
            hourly_temp = temp_df.groupby('hour')['temperature'].mean().to_dict()
            hourly_humid = humid_df.groupby('hour')['humidity'].mean().to_dict()
            
            return hourly_temp, hourly_humid
            
        except Exception as e:
            print(f"计算小时均值失败: {e}")
            return {}, {}
    
    def detect_spike(self, window=5, threshold=3.0):
        """检测突变点"""
        try:
            temps = self.temp_data.get_temperature_list()
            humids = self.humid_data.get_humidity_list()
            
            temp_spikes = []
            humid_spikes = []
            
            # 检测温度突变
            for i in range(window, len(temps)-window):
                prev_avg = sum(temps[i-window:i]) / window
                next_avg = sum(temps[i+1:i+window+1]) / window
                if abs(temps[i] - prev_avg) > threshold and abs(temps[i] - next_avg) > threshold:
                    temp_spikes.append(i)
            
            # 检测湿度突变
            for i in range(window, len(humids)-window):
                prev_avg = sum(humids[i-window:i]) / window
                next_avg = sum(humids[i+1:i+window+1]) / window
                if abs(humids[i] - prev_avg) > threshold and abs(humids[i] - next_avg) > threshold:
                    humid_spikes.append(i)
            
            return temp_spikes, humid_spikes
            
        except Exception as e:
            print(f"检测突变点失败: {e}")
            return [], []


class StaticPlotter:
    """静态图表绘制器类"""
    
    def __init__(self, temp_data_obj, humid_data_obj, analyzer):
        self.temp_data = temp_data_obj
        self.humid_data = humid_data_obj
        self.analyzer = analyzer
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_dual_axis(self, output_file='temperature_humidity_plot.png'):
        """绘制双Y轴曲线图"""
        try:
            fig, ax1 = plt.subplots(figsize=(12, 8))
            
            # 获取时间戳和数据处理
            timestamps = self.temp_data.get_timestamps()
            temperatures = self.temp_data.get_temperature_list()
            humidities = self.humid_data.get_humidity_list()
            
            # 确保数据长度一致
            min_len = min(len(timestamps), len(temperatures), len(humidities))
            timestamps = timestamps[:min_len]
            temperatures = temperatures[:min_len]
            humidities = humidities[:min_len]
            
            # 转换时间格式用于显示
            time_labels = [ts.split()[1][:5] for ts in timestamps]  # 只显示时分
            
            # 绘制温度曲线（红色）
            color = 'tab:red'
            ax1.set_xlabel('时间', fontsize=12)
            ax1.set_ylabel('温度 (°C)', color=color, fontsize=12)
            line1 = ax1.plot(time_labels, temperatures, color=color, linewidth=2, label='温度', marker='o', markersize=4)
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.set_ylim([min(temperatures)-5, max(temperatures)+5])
            
            # 标记温度异常点
            temp_anomalies = self.temp_data.get_anomaly_points()
            for anomaly in temp_anomalies:
                try:
                    idx = timestamps.index(anomaly['timestamp'])
                    ax1.plot(time_labels[idx], anomaly['temperature'], 'rx', markersize=10, markeredgewidth=2)
                except (ValueError, IndexError):
                    continue
            
            # 创建第二个Y轴用于湿度（蓝色）
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('湿度 (%)', color=color, fontsize=12)
            line2 = ax2.plot(time_labels, humidities, color=color, linewidth=2, label='湿度', linestyle='--', marker='s', markersize=4)
            ax2.tick_params(axis='y', labelcolor=color)
            ax2.set_ylim([min(humidities)-10, max(humidities)+10])
            
            # 标记湿度异常点
            humid_anomalies = self.humid_data.get_anomaly_points()
            for anomaly in humid_anomalies:
                try:
                    idx = timestamps.index(anomaly['timestamp'])
                    ax2.plot(time_labels[idx], anomaly['humidity'], 'bx', markersize=10, markeredgewidth=2)
                except (ValueError, IndexError):
                    continue
            
            # 设置X轴刻度
            step = max(1, len(time_labels) // 10)
            ax1.set_xticks(range(0, len(time_labels), step))
            ax1.set_xticklabels([time_labels[i] for i in range(0, len(time_labels), step)], rotation=45)
            
            # 添加标题和图例
            plt.title('温湿度监测曲线 (红色:温度, 蓝色:湿度, X标记:异常点)', fontsize=14, pad=20)
            
            # 合并图例
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # 添加网格
            ax1.grid(True, alpha=0.3)
            
            # 调整布局
            fig.tight_layout()
            
            # 保存图像
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"图表已保存为: {output_file} (300 DPI)")
            
            # 显示图表
            plt.show()
            
        except Exception as e:
            print(f"绘制图表失败: {e}")
            import traceback
            traceback.print_exc()


# ==================== 主程序部分 ====================

def main():
    """主程序"""
    print("=" * 60)
    print("温湿度环境监测系统")
    print("=" * 60)
    
    # 1. 读取数据
    print("\n1. 读取传感器数据...")
    reader = SensorDataReader()
    file_path = "sensor_log_202401.csv"
    
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在！")
        # 创建示例文件（仅用于测试）
        print("正在创建示例数据文件...")
        create_sample_data(file_path)
    
    clean_data = reader.read_csv(file_path)
    
    if not clean_data:
        print("警告: 没有读取到有效数据！")
        return
    
    # 2. 保存错误日志
    reader.save_error_log()
    
    # 3. 创建温度数据对象
    print("\n2. 创建温度数据对象...")
    temp_data = TemperatureData(clean_data)
    print(f"温度数据总数: {len(temp_data.temp_data)}")
    print(f"温度异常次数: {temp_data.get_anomaly_count()}")
    
    # 4. 创建湿度数据对象
    print("\n3. 创建湿度数据对象...")
    humid_data = HumidityData(clean_data)
    print(f"湿度数据总数: {len(humid_data.humid_data)}")
    print(f"湿度异常次数: {humid_data.get_anomaly_count()}")
    
    # 5. 数据分析
    print("\n4. 数据分析...")
    analyzer = DataAnalyzer(temp_data, humid_data)
    
    # 计算小时均值
    hourly_temp, hourly_humid = analyzer.calculate_hourly_average()
    print("温度小时均值:")
    for hour, temp in sorted(hourly_temp.items()):
        print(f"  {hour:02d}:00 - {temp:.2f}°C")
    
    print("湿度小时均值:")
    for hour, humid in sorted(hourly_humid.items()):
        print(f"  {hour:02d}:00 - {humid:.2f}%")
    
    # 检测突变点
    temp_spikes, humid_spikes = analyzer.detect_spike()
    print(f"温度突变点数量: {len(temp_spikes)}")
    print(f"湿度突变点数量: {len(humid_spikes)}")
    
    # 6. 数据可视化
    print("\n5. 生成可视化图表...")
    plotter = StaticPlotter(temp_data, humid_data, analyzer)
    plotter.plot_dual_axis()
    
    print("\n" + "=" * 60)
    print("系统运行完成！")
    print(f"有效数据: {len(clean_data)} 条")
    print(f"温度异常: {temp_data.get_anomaly_count()} 次")
    print(f"湿度异常: {humid_data.get_anomaly_count()} 次")
    print("=" * 60)


def create_sample_data(file_path):
    """创建示例数据文件（如果文件不存在）"""
    sample_data = """timestamp,temperature,humidity
2024-01-15 08:00:00,23.5,45.2
2024-01-15 08:05:00,24.1,46.8
2024-01-15 08:10:00,-5.0,120.0
2024-01-15 08:15:00,25.0,47.5
2024-01-15 08:20:00,25.8,48.2
2024-01-15 08:25:00,26.2,49.0
2024-01-15 08:30:00,26.5,48.5
2024-01-15 08:35:00,27.0,50.1
2024-01-15 08:40:00,27.3,51.0
2024-01-15 08:45:00,55.0,105.0
2024-01-15 08:50:00,27.8,49.5
2024-01-15 08:55:00,28.0,48.8
2024-01-15 09:00:00,28.2,49.2
2024-01-15 09:05:00,28.5,49.0
2024-01-15 09:10:00,28.8,48.5
2024-01-15 09:15:00,29.0,47.8
2024-01-15 09:20:00,29.2,48.0
2024-01-15 09:25:00,29.5,48.2
2024-01-15 09:30:00,29.8,48.5
2024-01-15 09:35:00,30.0,49.0
2024-01-15 09:40:00,30.2,49.5
2024-01-15 09:45:00,30.5,50.0
2024-01-15 09:50:00,30.8,49.8
2024-01-15 09:55:00,31.0,49.5
2024-01-15 10:00:00,31.2,49.2
2024-01-15 10:05:00,-10.0,invalid_humidity
2024-01-15 10:10:00,31.8,48.5
2024-01-15 10:15:00,32.0,48.2
2024-01-15 10:20:00,32.2,48.0
2024-01-15 10:25:00,32.5,47.8
2024-01-15 10:30:00,32.8,47.5
2024-01-15 10:35:00,33.0,47.2
2024-01-15 10:40:00,33.2,47.0
2024-01-15 10:45:00,33.5,46.8
2024-01-15 10:50:00,33.8,46.5
2024-01-15 10:55:00,34.0,46.2
2024-01-15 11:00:00,34.2,46.0
2024-01-15 11:05:00,34.5,45.8
2024-01-15 11:10:00,34.8,45.5
2024-01-15 11:15:00,35.0,45.2
2024-01-15 11:20:00,35.2,45.0
2024-01-15 11:25:00,35.5,44.8
2024-01-15 11:30:00,35.8,44.5
2024-01-15 11:35:00,36.0,44.2
2024-01-15 11:40:00,36.2,44.0
2024-01-15 11:45:00,36.5,43.8
2024-01-15 11:50:00,36.8,43.5
2024-01-15 11:55:00,37.0,43.2
2024-01-15 12:00:00,37.2,43.0
2024-01-15 12:05:00,37.5,42.8
2024-01-15 12:10:00,37.8,42.5
2024-01-15 12:15:00,38.0,42.2
2024-01-15 12:20:00,38.2,42.0
2024-01-15 12:25:00,38.5,41.8
2024-01-15 12:30:00,38.8,41.5
2024-01-15 12:35:00,39.0,41.2
2024-01-15 12:40:00,39.2,41.0
2024-01-15 12:45:00,39.5,40.8
2024-01-15 12:50:00,39.8,40.5
2024-01-15 12:55:00,40.0,40.2
2024-01-15 13:00:00,40.2,40.0
2024-01-15 13:05:00,40.5,39.8
2024-01-15 13:10:00,40.8,39.5
2024-01-15 13:15:00,60.0,150.0
2024-01-15 13:20:00,41.2,39.0
2024-01-15 13:25:00,41.5,38.8
2024-01-15 13:30:00,41.8,38.5
2024-01-15 13:35:00,42.0,38.2
2024-01-15 13:40:00,42.2,38.0
2024-01-15 13:45:00,42.5,37.8
2024-01-15 13:50:00,42.8,37.5
2024-01-15 13:55:00,43.0,37.2
2024-01-15 14:00:00,43.2,37.0
2024-01-15 14:05:00,43.5,36.8
2024-01-15 14:10:00,43.8,36.5
2024-01-15 14:15:00,44.0,36.2
2024-01-15 14:20:00,44.2,36.0
2024-01-15 14:25:00,44.5,35.8
2024-01-15 14:30:00,44.8,35.5
2024-01-15 14:35:00,45.0,35.2
2024-01-15 14:40:00,45.2,35.0
2024-01-15 14:45:00,45.5,34.8
2024-01-15 14:50:00,45.8,34.5
2024-01-15 14:55:00,46.0,34.2
2024-01-15 15:00:00,46.2,34.0
2024-01-15 15:05:00,46.5,33.8
2024-01-15 15:10:00,46.8,33.5
2024-01-15 15:15:00,47.0,33.2
2024-01-15 15:20:00,47.2,33.0
2024-01-15 15:25:00,47.5,32.8
2024-01-15 15:30:00,47.8,32.5
2024-01-15 15:35:00,48.0,32.2
2024-01-15 15:40:00,48.2,32.0
2024-01-15 15:45:00,48.5,31.8
2024-01-15 15:50:00,48.8,31.5
2024-01-15 15:55:00,49.0,31.2
2024-01-15 16:00:00,49.2,31.0
2024-01-15 16:05:00,49.5,30.8
2024-01-15 16:10:00,49.8,30.5
2024-01-15 16:15:00,50.0,30.2
2024-01-15 16:20:00,50.2,30.0
2024-01-15 16:25:00,50.5,29.8
2024-01-15 16:30:00,50.8,29.5
2024-01-15 16:35:00,51.0,29.2
2024-01-15 16:40:00,51.2,29.0
2024-01-15 16:45:00,51.5,28.8
2024-01-15 16:50:00,51.8,28.5
2024-01-15 16:55:00,52.0,28.2
2024-01-15 17:00:00,52.2,28.0"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(sample_data)
    print(f"示例数据文件已创建: {file_path}")


# ==================== GUI界面部分 ====================
# 以下为可选GUI实现，使用tkinter

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    class SensorMonitorApp:
        """传感器监测GUI应用程序"""
        
        def __init__(self, root):
            self.root = root
            self.root.title("温湿度环境监测系统")
            self.root.geometry("1200x800")
            
            # 初始化变量
            self.reader = None
            self.temp_data = None
            self.humid_data = None
            self.analyzer = None
            
            self.setup_ui()
        
        def setup_ui(self):
            """设置用户界面"""
            # 创建主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 配置网格权重
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)
            
            # 标题
            title_label = ttk.Label(main_frame, text="温湿度环境监测系统", 
                                   font=("Microsoft YaHei", 16, "bold"))
            title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
            
            # 文件选择部分
            ttk.Label(main_frame, text="数据文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.file_path_var = tk.StringVar(value="sensor_log_202401.csv")
            file_entry = ttk.Entry(main_frame, textvariable=self.file_path_var, width=50)
            file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            browse_btn = ttk.Button(main_frame, text="浏览...", command=self.browse_file)
            browse_btn.grid(row=1, column=2, padx=5, pady=5)
            
            # 控制按钮
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, columnspan=3, pady=10)
            
            load_btn = ttk.Button(button_frame, text="加载数据", command=self.load_data)
            load_btn.pack(side=tk.LEFT, padx=5)
            
            analyze_btn = ttk.Button(button_frame, text="分析数据", command=self.analyze_data)
            analyze_btn.pack(side=tk.LEFT, padx=5)
            
            plot_btn = ttk.Button(button_frame, text="生成图表", command=self.plot_data)
            plot_btn.pack(side=tk.LEFT, padx=5)
            
            export_btn = ttk.Button(button_frame, text="导出报告", command=self.export_report)
            export_btn.pack(side=tk.LEFT, padx=5)
            
            # 信息显示区域
            info_frame = ttk.LabelFrame(main_frame, text="数据信息", padding="10")
            info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
            info_frame.columnconfigure(0, weight=1)
            
            self.info_text = tk.Text(info_frame, height=10, width=80)
            info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
            self.info_text.configure(yscrollcommand=info_scroll.set)
            
            self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            info_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            # 图表显示区域
            chart_frame = ttk.LabelFrame(main_frame, text="温湿度图表", padding="10")
            chart_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
            chart_frame.columnconfigure(0, weight=1)
            chart_frame.rowconfigure(0, weight=1)
            
            self.chart_canvas = None
            
            # 配置主框架的行权重
            main_frame.rowconfigure(3, weight=1)
            main_frame.rowconfigure(4, weight=2)
        
        def browse_file(self):
            """浏览文件"""
            file_path = filedialog.askopenfilename(
                title="选择传感器数据文件",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
            )
            if file_path:
                self.file_path_var.set(file_path)
        
        def load_data(self):
            """加载数据"""
            file_path = self.file_path_var.get()
            
            if not os.path.exists(file_path):
                messagebox.showerror("错误", f"文件不存在: {file_path}")
                return
            
            try:
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "正在加载数据...\n")
                self.root.update()
                
                # 创建读取器并读取数据
                self.reader = SensorDataReader()
                clean_data = self.reader.read_csv(file_path)
                
                if not clean_data:
                    messagebox.showwarning("警告", "没有读取到有效数据！")
                    return
                
                # 保存错误日志
                self.reader.save_error_log()
                
                # 创建数据对象
                self.temp_data = TemperatureData(clean_data)
                self.humid_data = HumidityData(clean_data)
                
                # 显示信息
                self.info_text.insert(tk.END, "="*50 + "\n")
                self.info_text.insert(tk.END, "数据加载完成！\n")
                self.info_text.insert(tk.END, f"原始数据行数: {len(self.reader.raw_lines)}\n")
                self.info_text.insert(tk.END, f"有效数据行数: {len(clean_data)}\n")
                self.info_text.insert(tk.END, f"温度异常次数: {self.temp_data.get_anomaly_count()}\n")
                self.info_text.insert(tk.END, f"湿度异常次数: {self.humid_data.get_anomaly_count()}\n")
                self.info_text.insert(tk.END, f"错误日志已保存到: error.log\n")
                
                messagebox.showinfo("成功", "数据加载完成！")
                
            except Exception as e:
                messagebox.showerror("错误", f"加载数据失败: {e}")
                import traceback
                traceback.print_exc()
        
        def analyze_data(self):
            """分析数据"""
            if not self.temp_data or not self.humid_data:
                messagebox.showwarning("警告", "请先加载数据！")
                return
            
            try:
                self.analyzer = DataAnalyzer(self.temp_data, self.humid_data)
                
                # 计算小时均值
                hourly_temp, hourly_humid = self.analyzer.calculate_hourly_average()
                
                # 检测突变点
                temp_spikes, humid_spikes = self.analyzer.detect_spike()
                
                # 显示分析结果
                self.info_text.insert(tk.END, "\n" + "="*50 + "\n")
                self.info_text.insert(tk.END, "数据分析结果:\n")
                self.info_text.insert(tk.END, "\n温度小时均值:\n")
                for hour, temp in sorted(hourly_temp.items()):
                    self.info_text.insert(tk.END, f"  {hour:02d}:00 - {temp:.2f}°C\n")
                
                self.info_text.insert(tk.END, "\n湿度小时均值:\n")
                for hour, humid in sorted(hourly_humid.items()):
                    self.info_text.insert(tk.END, f"  {hour:02d}:00 - {humid:.2f}%\n")
                
                self.info_text.insert(tk.END, f"\n温度突变点数量: {len(temp_spikes)}\n")
                self.info_text.insert(tk.END, f"湿度突变点数量: {len(humid_spikes)}\n")
                
                messagebox.showinfo("成功", "数据分析完成！")
                
            except Exception as e:
                messagebox.showerror("错误", f"数据分析失败: {e}")
        
        def plot_data(self):
            """绘制图表"""
            if not self.temp_data or not self.humid_data or not self.analyzer:
                messagebox.showwarning("警告", "请先加载并分析数据！")
                return
            
            try:
                # 清除现有图表
                if self.chart_canvas:
                    self.chart_canvas.get_tk_widget().destroy()
                
                # 创建绘图器并绘制图表
                plotter = StaticPlotter(self.temp_data, self.humid_data, self.analyzer)
                
                # 创建新的图形
                fig = plt.figure(figsize=(10, 6))
                ax1 = fig.add_subplot(111)
                
                # 获取数据
                timestamps = self.temp_data.get_timestamps()
                temperatures = self.temp_data.get_temperature_list()
                humidities = self.humid_data.get_humidity_list()
                
                # 确保数据长度一致
                min_len = min(len(timestamps), len(temperatures), len(humidities))
                timestamps = timestamps[:min_len]
                temperatures = temperatures[:min_len]
                humidities = humidities[:min_len]
                
                time_labels = [ts.split()[1][:5] for ts in timestamps]
                
                # 绘制温度曲线
                color = 'tab:red'
                ax1.set_xlabel('时间', fontsize=10)
                ax1.set_ylabel('温度 (°C)', color=color, fontsize=10)
                line1 = ax1.plot(time_labels, temperatures, color=color, linewidth=1.5, label='温度')
                ax1.tick_params(axis='y', labelcolor=color)
                
                # 创建第二个Y轴
                ax2 = ax1.twinx()
                color = 'tab:blue'
                ax2.set_ylabel('湿度 (%)', color=color, fontsize=10)
                line2 = ax2.plot(time_labels, humidities, color=color, linewidth=1.5, label='湿度', linestyle='--')
                ax2.tick_params(axis='y', labelcolor=color)
                
                # 设置X轴刻度
                step = max(1, len(time_labels) // 10)
                ax1.set_xticks(range(0, len(time_labels), step))
                ax1.set_xticklabels([time_labels[i] for i in range(0, len(time_labels), step)], rotation=45)
                
                # 添加标题和图例
                plt.title('温湿度监测曲线', fontsize=12, pad=10)
                
                # 添加网格
                ax1.grid(True, alpha=0.3)
                
                # 调整布局
                fig.tight_layout()
                
                # 在GUI中显示图表
                self.chart_canvas = FigureCanvasTkAgg(fig, master=self.root.winfo_children()[0].winfo_children()[4])
                self.chart_canvas.draw()
                self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # 保存图表到文件
                plotter.plot_dual_axis()
                
                self.info_text.insert(tk.END, "\n图表生成完成！\n")
                
            except Exception as e:
                messagebox.showerror("错误", f"绘制图表失败: {e}")
                import traceback
                traceback.print_exc()
        
        def export_report(self):
            """导出报告"""
            if not self.temp_data or not self.humid_data:
                messagebox.showwarning("警告", "请先加载数据！")
                return
            
            try:
                file_path = filedialog.asksaveasfilename(
                    title="保存报告",
                    defaultextension=".txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("="*60 + "\n")
                        f.write("温湿度环境监测系统报告\n")
                        f.write("="*60 + "\n\n")
                        
                        f.write("1. 数据概览\n")
                        f.write("-"*40 + "\n")
                        f.write(f"数据文件: {self.file_path_var.get()}\n")
                        f.write(f"温度数据总数: {len(self.temp_data.temp_data)}\n")
                        f.write(f"湿度数据总数: {len(self.humid_data.humid_data)}\n")
                        f.write(f"温度异常次数: {self.temp_data.get_anomaly_count()}\n")
                        f.write(f"湿度异常次数: {self.humid_data.get_anomaly_count()}\n\n")
                        
                        if self.analyzer:
                            f.write("2. 分析结果\n")
                            f.write("-"*40 + "\n")
                            
                            hourly_temp, hourly_humid = self.analyzer.calculate_hourly_average()
                            f.write("温度小时均值:\n")
                            for hour, temp in sorted(hourly_temp.items()):
                                f.write(f"  {hour:02d}:00 - {temp:.2f}°C\n")
                            
                            f.write("\n湿度小时均值:\n")
                            for hour, humid in sorted(hourly_humid.items()):
                                f.write(f"  {hour:02d}:00 - {humid:.2f}%\n")
                            
                            temp_spikes, humid_spikes = self.analyzer.detect_spike()
                            f.write(f"\n温度突变点数量: {len(temp_spikes)}\n")
                            f.write(f"湿度突变点数量: {len(humid_spikes)}\n\n")
                        
                        f.write("3. 异常数据记录\n")
                        f.write("-"*40 + "\n")
                        if os.path.exists('error.log'):
                            with open('error.log', 'r', encoding='utf-8') as error_file:
                                f.write(error_file.read())
                    
                    messagebox.showinfo("成功", f"报告已保存到: {file_path}")
                    
            except Exception as e:
                messagebox.showerror("错误", f"导出报告失败: {e}")
    
    def run_gui():
        """运行GUI应用程序"""
        root = tk.Tk()
        app = SensorMonitorApp(root)
        root.mainloop()

except ImportError:
    print("注意: tkinter未安装，GUI功能不可用")
    print("如需GUI功能，请安装python-tk或使用命令行的主程序")
    run_gui = None

# ==================== 运行程序 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="温湿度环境监测系统")
    parser.add_argument('--gui', action='store_true', help='使用GUI界面')
    parser.add_argument('--file', type=str, default='sensor_log_202401.csv', help='数据文件路径')
    
    args = parser.parse_args()
    
    if args.gui and run_gui:
        run_gui()
    else:
        # 设置文件路径
        if args.file != 'sensor_log_202401.csv':
            # 如果指定了文件，需要修改主程序中的文件路径
            import types
            main_module = sys.modules['__main__']
            
            # 修改main函数中的文件路径
            original_main = main
            
            def modified_main():
                print(f"使用数据文件: {args.file}")
                # 这里需要修改main函数中的文件路径
                # 由于main函数中直接使用字符串，我们创建一个新的main函数
                print("=" * 60)
                print("温湿度环境监测系统")
                print("=" * 60)
                
                # 1. 读取数据
                print("\n1. 读取传感器数据...")
                reader = SensorDataReader()
                file_path = args.file
                
                if not os.path.exists(file_path):
                    print(f"错误: 文件 '{file_path}' 不存在！")
                    return
                
                clean_data = reader.read_csv(file_path)
                
                if not clean_data:
                    print("警告: 没有读取到有效数据！")
                    return
                
                # 其余代码与原始main函数相同...
                # 这里省略重复代码，直接调用原始main的逻辑
                # 2. 保存错误日志
                reader.save_error_log()
                
                # 3. 创建温度数据对象
                print("\n2. 创建温度数据对象...")
                temp_data = TemperatureData(clean_data)
                print(f"温度数据总数: {len(temp_data.temp_data)}")
                print(f"温度异常次数: {temp_data.get_anomaly_count()}")
                
                # 4. 创建湿度数据对象
                print("\n3. 创建湿度数据对象...")
                humid_data = HumidityData(clean_data)
                print(f"湿度数据总数: {len(humid_data.humid_data)}")
                print(f"湿度异常次数: {humid_data.get_anomaly_count()}")
                
                # 5. 数据分析
                print("\n4. 数据分析...")
                analyzer = DataAnalyzer(temp_data, humid_data)
                
                # 计算小时均值
                hourly_temp, hourly_humid = analyzer.calculate_hourly_average()
                print("温度小时均值:")
                for hour, temp in sorted(hourly_temp.items()):
                    print(f"  {hour:02d}:00 - {temp:.2f}°C")
                
                print("湿度小时均值:")
                for hour, humid in sorted(hourly_humid.items()):
                    print(f"  {hour:02d}:00 - {humid:.2f}%")
                
                # 检测突变点
                temp_spikes, humid_spikes = analyzer.detect_spike()
                print(f"温度突变点数量: {len(temp_spikes)}")
                print(f"湿度突变点数量: {len(humid_spikes)}")
                
                # 6. 数据可视化
                print("\n5. 生成可视化图表...")
                plotter = StaticPlotter(temp_data, humid_data, analyzer)
                plotter.plot_dual_axis()
                
                print("\n" + "=" * 60)
                print("系统运行完成！")
                print(f"有效数据: {len(clean_data)} 条")
                print(f"温度异常: {temp_data.get_anomaly_count()} 次")
                print(f"湿度异常: {humid_data.get_anomaly_count()} 次")
                print("=" * 60)
            
            modified_main()
        else:
            main()
