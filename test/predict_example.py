"""
完整的模型训练测试脚本
测试流程包括：
1. 数据准备验证
2. 多模型训练对比
3. 模型性能评估
4. 价格预测测试
5. 结果可视化

运行方式：
    conda activate agri
    cd d:\ai\test
    python model_training_test.py
"""

import requests
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

API_BASE = "http://localhost:8000"

def check_backend_health():
    """检查后端服务是否正常运行"""
    try:
        resp = requests.get(f"{API_BASE}/docs")
        if resp.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 后端服务异常: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        return False

def get_supported_models():
    """获取支持的模型列表"""
    try:
        resp = requests.get(f"{API_BASE}/api/predict/models")
        resp.raise_for_status()
        models = resp.json().get("models", [])
        print(f"📊 支持的模型: {models}")
        return models
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return []

def check_data_availability():
    """检查数据可用性"""
    try:
        # 尝试获取价格数据概览
        resp = requests.get(f"{API_BASE}/api/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            print("📈 数据概览:")
            print(f"  - 当日白菜均价: {data.get('today_cabbage_price', 'N/A')} 元/公斤")
            print(f"  - 当日土豆均价: {data.get('today_potato_price', 'N/A')} 元/公斤")
            print(f"  - 未读预警数量: {data.get('alert_unread_count', 0)}")
            return True
        else:
            print(f"⚠️  获取数据概览失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查数据可用性失败: {e}")
        return False

def train_multiple_models(product_name="本地白菜", train_ratio=0.8):
    """训练多个模型并对比性能"""
    models = get_supported_models()
    if not models:
        print("❌ 没有可用的模型")
        return None

    print(f"\n🚀 开始训练模型: {product_name}")
    print("=" * 50)

    train_body = {
        "product_name": product_name,
        "models": models,
        "train_ratio": train_ratio,
        "cv_folds": 3  # 减少交叉验证折数以加快测试
    }

    try:
        print("正在训练模型...")
        start_time = time.time()
        resp = requests.post(f"{API_BASE}/api/predict/train", json=train_body)
        training_time = time.time() - start_time

        if not resp.ok:
            print(f"❌ 训练失败: {resp.status_code} - {resp.text}")
            return None

        results = resp.json().get("results", [])

        print(f"✅ 训练完成 (耗时: {training_time:.2f}秒)")
        print("\n📊 模型性能对比:")
        print("-" * 80)
        print(f"{'模型名称':<15} {'MAE':<10} {'RMSE':<10} {'MAPE(%)':<10} {'状态':<10}")
        print("-" * 80)

        performance_data = []
        for result in results:
            model_name = result["model_name"]
            if "error" in result:
                status = f"❌ {result['error'][:15]}..."
                print(f"{model_name:<15} {'-':<10} {'-':<10} {'-':<10} {status:<10}")
            else:
                mae = result["mae"]
                rmse = result["rmse"]
                mape = result["mape"]
                status = "✅ 成功"
                performance_data.append({
                    'model': model_name,
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape
                })
                print(f"{model_name:<15} {mae:<10.4f} {rmse:<10.4f} {mape:<10.2f} {status:<10}")

        return performance_data

    except Exception as e:
        print(f"❌ 训练过程中发生错误: {e}")
        return None

def predict_with_best_model(product_name="本地白菜", predict_days=7):
    """使用最佳模型进行预测"""
    models = get_supported_models()
    if not models:
        return None

    # 使用第一个可用模型进行预测测试
    model_name = models[0]
    print(f"\n🔮 使用模型 {model_name} 进行 {predict_days} 天预测")
    print("=" * 50)

    predict_body = {
        "product_name": product_name,
        "model_name": model_name,
        "predict_days": predict_days,
        "use_weather": True
    }

    try:
        resp = requests.post(f"{API_BASE}/api/predict/predict", json=predict_body)
        if not resp.ok:
            print(f"❌ 预测失败: {resp.status_code} - {resp.text}")
            return None

        data = resp.json()
        print(f"✅ 预测完成")
        print(f"产品: {data['product_name']}")
        print(f"模型: {data['model_name']}")

        if data.get('metrics'):
            m = data['metrics']
            print(f"模型评估指标: MAE={m['mae']:.4f}, RMSE={m['rmse']:.4f}, MAPE={m['mape']:.2f}%")

        print(f"\n未来 {predict_days} 天价格预测:")
        print("-" * 60)
        predictions = []
        for item in data["predictions"]:
            pred_date = item['predict_date']
            price = item['price_pred']
            low = item.get('confidence_low', 'N/A')
            high = item.get('confidence_high', 'N/A')
            predictions.append({
                'date': pred_date,
                'price': price,
                'low': low,
                'high': high
            })
            print(f"{pred_date}: {price:.2f} 元/公斤 (置信区间: [{low:.2f}, {high:.2f}])")

        return predictions

    except Exception as e:
        print(f"❌ 预测过程中发生错误: {e}")
        return None

def visualize_results(performance_data, predictions):
    """可视化训练结果和预测结果"""
    try:
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 绘制模型性能对比图
        if performance_data:
            df_perf = pd.DataFrame(performance_data)
            x = range(len(df_perf))
            width = 0.25

            ax1.bar([i - width for i in x], df_perf['mae'], width, label='MAE', alpha=0.8)
            ax1.bar(x, df_perf['rmse'], width, label='RMSE', alpha=0.8)
            ax1.bar([i + width for i in x], df_perf['mape'], width, label='MAPE(%)', alpha=0.8)

            ax1.set_xlabel('模型')
            ax1.set_ylabel('数值')
            ax1.set_title('模型性能对比')
            ax1.set_xticks(x)
            ax1.set_xticklabels(df_perf['model'])
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # 绘制预测趋势图
        if predictions:
            df_pred = pd.DataFrame(predictions)
            df_pred['date'] = pd.to_datetime(df_pred['date'])

            ax2.plot(df_pred['date'], df_pred['price'], 'o-', linewidth=2, markersize=6, label='预测价格')
            ax2.fill_between(df_pred['date'], df_pred['low'], df_pred['high'], alpha=0.3, label='置信区间')

            ax2.set_xlabel('日期')
            ax2.set_ylabel('价格 (元/公斤)')
            ax2.set_title('价格预测趋势')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig(f'model_training_results_{timestamp}.png', dpi=300, bbox_inches='tight')
        print(f"📊 结果图表已保存为: model_training_results_{timestamp}.png")
        plt.show()

    except Exception as e:
        print(f"⚠️ 图表生成失败: {e}")

def run_comprehensive_test():
    """运行完整的测试流程"""
    print("🌾 农产品价格预测系统 - 模型训练测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 检查后端服务
    if not check_backend_health():
        return

    # 2. 检查数据可用性
    if not check_data_availability():
        print("⚠️ 建议先加载测试数据再运行训练测试")

    # 3. 训练模型
    performance_data = train_multiple_models("本地白菜", 0.8)

    # 4. 进行预测
    predictions = predict_with_best_model("本地白菜", 7)

    # 5. 可视化结果
    if performance_data or predictions:
        visualize_results(performance_data, predictions)

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_comprehensive_test()
