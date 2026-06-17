#!/usr/bin/env python3
"""为每篇教程添加FAQ、调试清单、交叉引用"""
import os, re

TUTORIALS_DIR = os.path.join(os.path.dirname(__file__), "static", "tutorials")

# 各教程的FAQ和调试清单数据
TUTORIAL_DATA = {
    "main": {
        "title": "嵌入式小白完全指南",
        "faq": [
            ("STM32和Arduino哪个先学？", "如果你目标是做产品，先学STM32（寄存器级理解）；如果想快速出原型，先学Arduino。建议：先STM32打基础，Arduino当工具。"),
            ("需要学51单片机吗？", "不必须。51架构古老，但教学资源丰富。如果学校课程用51，跟着学；否则直接STM32更高效。"),
            ("HAL库和寄存器操作哪个好？", "初学用HAL库快速上手，但要理解底层寄存器原理。工作后两种都要会。"),
            ("C语言要学到什么程度？", "至少掌握：指针、结构体、位操作、volatile关键字、回调函数。不需要学C++面向对象。"),
        ],
        "related": ["arm-gcc", "stm32", "serial", "flash-debug"],
    },
    "arm-gcc": {
        "title": "ARM GCC工具链",
        "faq": [
            ("arm-none-eabi-gcc和普通gcc有什么区别？", "arm-none-eabi是ARM裸机交叉编译器，没有操作系统依赖；普通gcc编译x86本机程序。嵌入式必须用交叉编译器。"),
            ("为什么编译成功但烧录后没反应？", "常见原因：1)链接脚本(.ld)中FLASH/RAM地址错误 2)未调用SystemInit() 3)中断向量表未正确放置 4)时钟配置错误"),
            ("-O2和-Os优化选哪个？", "嵌入式通常用-Os（优化代码体积），RAM/Flash有限时更重要。-O2速度更快但体积大。调试时用-O0。"),
        ],
        "related": ["makefile", "cmake", "stm32", "flash-debug"],
    },
    "cmake": {
        "title": "CMake构建系统",
        "faq": [
            ("CMake和Makefile哪个好？", "小项目Makefile够用，大项目（多模块/跨平台）CMake更方便。嵌入式推荐CMake+pico-sdk或zephyr方式。"),
            ("交叉编译怎么配置？", "需要toolchain文件：set(CMAKE_SYSTEM_NAME Generic) + set(CMAKE_C_COMPILER arm-none-eabi-gcc)，然后用 cmake -DCMAKE_TOOLCHAIN_FILE=arm.cmake .."),
            ("CMake和STM32CubeMX冲突吗？", "不冲突。CubeMX生成代码，CMake管理编译。可以用CubeMX生成后用CMake构建。"),
        ],
        "related": ["makefile", "arm-gcc", "stm32"],
    },
    "makefile": {
        "title": "Makefile实战",
        "faq": [
            ("Makefile中$@和$<是什么？", "$@=目标名，$<=第一个依赖，$^=所有依赖。例：%.o: %.c → $@是%.o，$<是%.c"),
            ("为什么修改了头文件但make没重新编译？", "需要在依赖中包含头文件：$(OBJ): $(SRC) $(HEADERS)，或用gcc -MMD自动生成依赖。"),
            ("make -j4是什么意思？", "4个并行编译任务，加快编译速度。CPU核心数就是最佳并行数。"),
        ],
        "related": ["arm-gcc", "cmake"],
    },
    "flash-debug": {
        "title": "烧录与调试",
        "faq": [
            ("ST-Link和J-Link哪个好？", "ST-Link便宜（克隆版¥8），只支持ST芯片；J-Link贵（¥200+），支持所有ARM芯片且速度快。初学用ST-Link够了。"),
            ("烧录失败怎么排查？", "1)检查SWD接线(SWDIO/SWCLK/GND/VCC) 2)检查芯片是否锁死(Option Bytes) 3)检查供电电压(3.3V) 4)OpenOCD看输出日志"),
            ("HardFault怎么调试？", "1)在HardFault_Handler中设断点 2)查看LR寄存器判断是MSP还是PSP 3)从栈中提取PC值 4)用addr2line定位源码行"),
        ],
        "related": ["arm-gcc", "stm32", "serial"],
    },
    "serial": {
        "title": "串口通信",
        "faq": [
            ("串口收不到数据？", "排查：1)TX/RX交叉接(TX接RX) 2)波特率一致 3)GND共地 4)用示波器/逻辑分析仪抓波形 5)检查DMA配置"),
            ("printf怎么重定向到串口？", "重写fputc函数：int fputc(int ch, FILE *f) { HAL_UART_Transmit(&huart1, (uint8_t*)&ch, 1, 100); return ch; }，还要勾选Use MicroLIB或实现_syscalls"),
            ("115200波特率够用吗？", "一般调试够用。传输大量数据（如ADC波形）需要921600或USB CDC。距离>10米需要RS485。"),
        ],
        "related": ["stm32", "protocols", "flash-debug"],
    },
    "stm32": {
        "title": "STM32开发",
        "faq": [
            ("F103和F407选哪个？", "F103(72MHz/Cortex-M3/64KB Flash)够入门；F407(168MHz/Cortex-M4/512KB Flash)有FPU和DSP指令，做信号处理/BCI必备。"),
            ("HAL库太臃肿怎么办？", "1)用LL库（更底层但代码少）2)用寄存器直接操作 3)CubeMX选择只生成需要的模块 4)开启编译优化-Os"),
            ("时钟树怎么配？", "初学用CubeMX自动配。关键：外部晶振→PLL倍频→SYSCLK。F407典型：8MHz晶振×7=168MHz。"),
            ("中断优先级怎么设？", "数字越小优先级越高。FreeRTOS需设5位优先级（NVIC_PriorityGroupConfig(4)）。SysTick和PendSV设最低优先级。"),
        ],
        "related": ["arm-gcc", "serial", "flash-debug", "freertos", "protocols"],
    },
    "esp32": {
        "title": "ESP32开发",
        "faq": [
            ("ESP32用Arduino还是ESP-IDF？", "快速原型用Arduino，产品开发用ESP-IDF。ESP-IDF有更好的FreeRTOS集成和功耗管理。"),
            ("ESP32和STM32哪个好？", "不同定位：ESP32适合WiFi/BLE/IoT场景，STM32适合实时控制/低功耗。做IoT选ESP32，做电机控制选STM32。"),
            ("ESP32功耗怎么优化？", "Deep Sleep模式下10μA，定时唤醒或GPIO唤醒。Light Sleep约0.8mA。WiFi发射时约200mA。"),
        ],
        "related": ["stm32", "proj-esp32-iot", "freertos"],
    },
    "freertos": {
        "title": "FreeRTOS入门",
        "faq": [
            ("FreeRTOS和裸机开发哪个好？", "3个以上并发任务用RTOS更清晰。1~2个任务裸机+状态机更简单。不要为了用RTOS而用RTOS。"),
            ("任务栈大小怎么设？", "初期设256或512字（word），用uxTaskGetStackHighWaterMark()查看实际用量，再减半+20%余量。"),
            ("优先级反转怎么办？", "使用互斥量(Mutex)替代二值信号量，FreeRTOS的Mutex自带优先级继承机制。"),
            ("vTaskDelay和vTaskDelayUntil区别？", "vTaskDelay是相对延时（从调用时刻起），vTaskDelayUntil是绝对周期（适合精确周期任务）。推荐用DelayUntil做采样循环。"),
        ],
        "related": ["stm32", "proj-freertos-station", "proj-smart-car", "proj-low-power"],
    },
    "protocols": {
        "title": "通信协议I2C/SPI/UART/CAN",
        "faq": [
            ("I2C和SPI选哪个？", "速度优先选SPI(可达几十MHz)，引脚少选I2C(只需2根)。传感器多选I2C，Flash/屏选SPI。"),
            ("I2C总线卡死怎么办？", "从机拉低SDA不释放。解决：1)重新初始化I2C 2)发9个SCL时钟脉冲 3)GPIO模拟I2C复位序列 4)硬件上加拉电阻4.7kΩ"),
            ("CAN和RS485哪个好？", "CAN有仲裁机制和错误处理，适合多主高可靠场景（汽车）；RS485简单便宜，适合主从式长距离通信。"),
        ],
        "related": ["serial", "stm32", "proj-can-bus"],
    },
    # 项目教程
    "proj-led-button": {
        "title": "LED跑马灯+按键控制",
        "faq": [
            ("LED亮度不一样？", "不同颜色LED正向压降不同（红2V/蓝3V），需要不同限流电阻。简单做法：统一用1kΩ电阻。"),
            ("按键抖动怎么办？", "硬件：0.1μF电容滤波。软件：延时10~20ms消抖。推荐：定时器扫描+状态机消抖（不阻塞）。"),
        ],
        "related": ["stm32", "proj-uart-hello", "proj-oled-display"],
    },
    "proj-uart-hello": {
        "title": "串口Hello World",
        "faq": [
            ("中文乱码？", "确保发送端和接收端编码都是UTF-8。PuTTY设置Window→Translation→UTF-8。代码中字符串加u8前缀。"),
            ("DMA接收丢数据？", "1)DMA缓冲区要4字节对齐 2)用空闲中断(IDLE)处理不定长数据 3)双缓冲防数据覆盖"),
        ],
        "related": ["serial", "proj-oled-display", "proj-dht11-monitor"],
    },
    "proj-oled-display": {
        "title": "OLED显示屏驱动",
        "faq": [
            ("OLED不亮？", "1)I2C地址扫描(0x3C或0x3D) 2)SDA/SCL上拉电阻4.7kΩ 3)供电3.3V（不是5V！）"),
            ("显示花屏？", "1)刷新率太快导致I2C拥堵 2)显存buffer未清零 3)坐标计算越界（0~127×0~63）"),
        ],
        "related": ["proj-dht11-monitor", "proj-freertos-station"],
    },
    "proj-dht11-monitor": {
        "title": "DHT11温湿度监测",
        "faq": [
            ("DHT11读取失败？", "1)时序要求严格，禁用中断再读 2)起始信号拉低18ms 3)数据线需要4.7kΩ上拉 4)换DHT22精度更高"),
            ("温度精度差？", "DHT11精度±2°C，DHT22精度±0.5°C。高精度场景用DS18B20或SHT30。"),
        ],
        "related": ["proj-oled-display", "proj-freertos-station"],
    },
    "proj-pwm-motor": {
        "title": "PWM直流电机控制",
        "faq": [
            ("电机不转？", "1)PWM频率太高/太低（1~20kHz合适） 2)L298N使能脚未拉高 3)供电不足（电机需要独立电源）"),
            ("电机啸叫？", "PWM频率在人耳范围(20Hz~20kHz)，改到20kHz以上听不到。但太高开关损耗大，折中选16~25kHz。"),
        ],
        "related": ["proj-servo-control", "proj-stepper-motor", "proj-smart-car"],
    },
    "proj-servo-control": {
        "title": "舵机控制",
        "faq": [
            ("舵机抖动？", "1)PWM信号不稳定（用定时器硬件PWM不要软件模拟） 2)供电不足（舵机峰值电流>500mA） 3)负载过大"),
            ("角度不准？", "校准0.5ms~2.5ms对应0°~180°。不同舵机范围不同，需要实测。"),
        ],
        "related": ["proj-pwm-motor", "proj-stepper-motor"],
    },
    "proj-ir-remote": {
        "title": "红外遥控解码",
        "faq": [
            ("解码不稳定？", "1)用输入捕获不要轮询 2)定时器时钟精度够高(1MHz以上) 3)加状态机容错 4)屏蔽重复码"),
            ("不同遥控器协议不同？", "最常见NEC协议。还有Sony SIRC、Philips RC-5。一般只支持NEC就够了。"),
        ],
        "related": ["proj-smart-car", "proj-led-button"],
    },
    "proj-ultrasonic": {
        "title": "超声波测距",
        "faq": [
            ("测距不准？", "1)声速随温度变化(331.4+0.6T m/s)需温度补偿 2)超过4m回波太弱 3)盲区<2cm无法测"),
            ("多传感器互相干扰？", "时分复用：依次触发每个传感器，等回波结束后再触发下一个。"),
        ],
        "related": ["proj-smart-car", "proj-pwm-motor"],
    },
    "proj-stepper-motor": {
        "title": "步进电机控制",
        "faq": [
            ("步进电机丢步？", "1)加速度太大，需要梯形/S形加减速曲线 2)负载过重 3)驱动电压不够 4)脉冲频率突变"),
            ("28BYJ-48为什么转得慢？", "减速比1:64，实际步距角5.625°/64=0.088°。需要高速时换NEMA17+A4988驱动。"),
        ],
        "related": ["proj-pwm-motor", "proj-servo-control"],
    },
    "proj-freertos-station": {
        "title": "FreeRTOS环境监测站",
        "faq": [
            ("任务间数据怎么传？", "1)队列(xQueueSend/Receive)最安全 2)全局变量+互斥量 3)事件组(EventGroup)适合同步 4)流缓冲区(StreamBuffer)适合DMA数据"),
            ("系统跑飞？", "1)栈溢出（增大任务栈） 2)优先级设置不合理 3)中断中调用了非ISR安全API 4)看门狗超时"),
        ],
        "related": ["freertos", "proj-dht11-monitor", "proj-oled-display", "proj-sd-logger"],
    },
    "proj-smart-car": {
        "title": "智能小车",
        "faq": [
            ("小车跑偏？", "1)左右电机速度差（需单独校准PWM） 2)轮径不一致 3)电池电压下降导致速度变化 → 需要编码器+PID闭环"),
            ("避障反应慢？", "1)超声波测距周期太长（降到50ms） 2)决策逻辑太复杂 3)电机响应延迟 → 提高控制频率到100Hz"),
        ],
        "related": ["proj-pwm-motor", "proj-ultrasonic", "proj-ir-remote", "proj-freertos-station"],
    },
    "proj-can-bus": {
        "title": "CAN总线通信",
        "faq": [
            ("CAN通信不上？", "1)两个节点波特率必须一致 2)CAN_H和CAN_L不要接反 3)需要120Ω终端电阻 4)至少2个节点才能正常通信"),
            ("CAN过滤器怎么配？", "STM32 CAN过滤器有列表模式和掩码模式。初学用列表模式（精确匹配ID），高级用掩码模式（范围过滤）。"),
        ],
        "related": ["protocols", "proj-s32k144-auto"],
    },
    "proj-sd-logger": {
        "title": "SD卡数据记录仪",
        "faq": [
            ("SD卡初始化失败？", "1)SPI模式需先发80个时钟 2)供电3.3V（某些卡需5V） 3)换一张卡试试（卡兼容性问题常见） 4)FatFS版本要新"),
            ("写入速度慢？", "1)单次写入512字节对齐 2)用f_sync()代替频繁f_close() 3)SD卡Class等级影响写入速度 4)避免频繁打开关闭文件"),
        ],
        "related": ["proj-freertos-station", "proj-dht11-monitor", "proj-bootloader-iap"],
    },
    "proj-esp32-iot": {
        "title": "ESP32 WiFi物联网",
        "faq": [
            ("WiFi连接不上？", "1)SSID/密码正确 2)2.4GHz不是5GHz 3)WiFi.begin()后等WL_CONNECTED 4)路由器MAC过滤 5)ESP32离路由器太远"),
            ("MQTT断线重连？", "1)设setKeepAlive(60) 2)设setCleanSession(true) 3)loop()中检查连接状态 4)指数退避重连"),
        ],
        "related": ["esp32", "proj-freertos-station", "proj-dht11-monitor"],
    },
    "proj-low-power": {
        "title": "低功耗电池设备",
        "faq": [
            ("功耗降不下来？", "1)未用GPIO设为模拟输入 2)关闭不需要的外设时钟 3)ADC用完关闭 4)printf/UART是功耗大户 5)检查是否有上拉电阻持续耗电"),
            ("Standby模式唤醒后程序从头跑？", "对，Standby是最深度休眠，唤醒等同复位。需要保存数据到RTC后备寄存器或外部EEPROM。Stop模式可保持RAM。"),
        ],
        "related": ["freertos", "stm32", "proj-freertos-station"],
    },
    "proj-bootloader-iap": {
        "title": "Bootloader IAP升级",
        "faq": [
            ("升级后程序跑飞？", "1)向量表偏移未修改(VTOR) 2)bin文件偏移地址错误 3)Flash写入未对齐(64位) 4)升级过程中断电→需双分区方案"),
            ("如何防变砖？", "1)A/B双分区方案 2)升级前校验CRC 3)Bootloader永不更新 4)保留串口回退升级通道"),
        ],
        "related": ["proj-sd-logger", "proj-esp32-iot", "flash-debug"],
    },
    "proj-dma-adc": {
        "title": "DMA双缓冲ADC采集",
        "faq": [
            ("ADC数据跳变？", "1)模拟输入阻抗太高（加运放缓冲） 2)采样时间太短（增大ADC采样周期） 3)参考电压不稳（加去耦电容） 4)数字噪声干扰（模拟地数字地分开）"),
            ("DMA传输完成中断不触发？", "1)检查DMA模式和通道配置 2)NVIC使能DMA中断 3)ADC连续采样模式 4)缓冲区大小是DMA传输数据量的整数倍"),
        ],
        "related": ["stm32", "bci-2026", "proj-oscilloscope-debug"],
    },
    "proj-usb-hid": {
        "title": "USB HID键盘鼠标",
        "faq": [
            ("电脑识别不到USB设备？", "1)USB DP需要1.5kΩ上拉到3.3V（全速设备） 2)描述符格式必须严格符合USB规范 3)VBus检测引脚配置 4)时钟精度要求±0.25%"),
            ("HID报表描述符怎么写？", "用USB HID Descriptor Tool生成。初学参考STM32 CubeMX自动生成的模板，不要手写。"),
        ],
        "related": ["stm32", "freertos"],
    },
    "proj-s32k144-auto": {
        "title": "S32K144汽车电子",
        "faq": [
            ("S32DS和STM32CubeIDE区别？", "S32DS基于Eclipse，专用于NXP芯片，有AUTOSAR工具链。STM32CubeIDE用于ST芯片。两者不互通。"),
            ("汽车电子和普通嵌入式区别？", "1)功能安全(ISO 26262) 2)更严格的EMC要求 3)更长的产品生命周期(10~15年) 4)ASIL等级 5)更复杂的网络(CAN/LIN/FlexRay)"),
        ],
        "related": ["proj-can-bus", "freertos"],
    },
    "proj-oscilloscope-debug": {
        "title": "示波器调试实战",
        "faq": [
            ("没有示波器怎么办？", "1)逻辑分析仪(¥60)可看数字信号 2)Saleae软件很强大 3)STM32的GPIO翻转+逻辑分析仪替代 4)SoundCard示波器(用声卡)看低频信号"),
            ("如何测量中断延迟？", "在中断入口翻转GPIO(拉高)，处理完再拉低。示波器测量GPIO高电平宽度=中断处理时间。触发信号用外部中断源。"),
        ],
        "related": ["flash-debug", "proj-dma-adc"],
    },
}

def add_faq_and_references():
    """为每篇教程添加FAQ和交叉引用"""
    for page_id, data in TUTORIAL_DATA.items():
        filename = f"{page_id}.html"
        path = os.path.join(TUTORIALS_DIR, filename)
        
        if not os.path.exists(path):
            print(f"  ⚠️ {filename} 不存在，跳过")
            continue
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已有FAQ
        if "常见问题" in content and "FAQ" in content.upper():
            print(f"  ⏭️ {filename} 已有FAQ，跳过")
            continue
        
        # 构建FAQ HTML
        faq_html = f"""
<hr><h2>❓ 常见问题 FAQ</h2>
"""
        for q, a in data["faq"]:
            faq_html += f"""
<div style="margin:12px 0;padding:12px 16px;background:var(--bg2);border-left:3px solid var(--a);border-radius:0 8px 8px 0">
  <p style="font-weight:600;color:var(--c1);margin-bottom:4px">Q: {q}</p>
  <p style="color:var(--t)">A: {a}</p>
</div>
"""
        
        # 构建交叉引用HTML
        related_html = ""
        if data.get("related"):
            related_html = """
<hr><h2>🔗 相关教程</h2>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0">
"""
            related_titles = {
                "main": "小白完全指南", "arm-gcc": "ARM GCC", "cmake": "CMake", "makefile": "Makefile",
                "flash-debug": "烧录与调试", "serial": "串口通信", "stm32": "STM32开发", "esp32": "ESP32开发",
                "freertos": "FreeRTOS", "protocols": "通信协议",
                "proj-led-button": "LED+按键", "proj-uart-hello": "串口Hello", "proj-oled-display": "OLED显示",
                "proj-dht11-monitor": "温湿度", "proj-pwm-motor": "PWM电机", "proj-servo-control": "舵机",
                "proj-ir-remote": "红外遥控", "proj-ultrasonic": "超声波", "proj-stepper-motor": "步进电机",
                "proj-freertos-station": "FreeRTOS站", "proj-smart-car": "智能小车", "proj-can-bus": "CAN总线",
                "proj-sd-logger": "SD卡记录", "proj-esp32-iot": "ESP32 IoT", "proj-low-power": "低功耗",
                "proj-bootloader-iap": "Bootloader", "proj-dma-adc": "DMA+ADC", "proj-usb-hid": "USB HID",
                "proj-s32k144-auto": "汽车电子", "proj-oscilloscope-debug": "示波器调试", "bci-2026": "BCI 2026",
            }
            for rid in data["related"]:
                rtitle = related_titles.get(rid, rid)
                related_html += f'<a href="#" onclick="parent.loadPage && parent.loadPage(\'{rid}\')" style="display:inline-block;padding:6px 14px;background:var(--bg3);border:1px solid var(--br);border-radius:6px;color:var(--a);text-decoration:none;font-size:.85em">{rtitle} →</a>\n'
            related_html += "</div>\n"
        
        # 在</body>前插入
        insert_pos = content.rfind("</body>")
        if insert_pos < 0:
            insert_pos = len(content)
        
        content = content[:insert_pos] + faq_html + related_html + "\n" + content[insert_pos:]
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"  ✅ {filename} 添加FAQ({len(data['faq'])}条)+交叉引用({len(data.get('related',[]))}个)")

print("为教程添加FAQ和交叉引用...")
add_faq_and_references()
print("✅ 全部完成！")
