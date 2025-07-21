"""
测试 check_service_status() 函数可用性的专用程序
"""

import sys
import traceback
from datetime import datetime

print("=== 测试 check_service_status() 函数可用性 ===")
print(f"测试时间: {datetime.now()}")
print()

def test_function_basic():
    """基础功能测试"""
    
    print("🔧 步骤1: 基础功能测试...")
    
    try:
        # 1. 导入测试
        print("📦 导入 check_service_status 函数...")
        from tradingagents.api.stock_api import check_service_status
        print("✅ 函数导入成功")
        
        # 2. 调用测试
        print("🚀 调用 check_service_status()...")
        result = check_service_status()
        print("✅ 函数调用成功")
        
        # 3. 返回值类型检查
        print(f"📋 返回值类型: {type(result)}")
        if isinstance(result, dict):
            print("✅ 返回值是字典类型")
        else:
            print(f"❌ 返回值不是字典类型: {type(result)}")
            return False
        
        # 4. 显示完整结果
        print("\n📊 完整返回结果:")
        print("-" * 60)
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("-" * 60)
        
        return True, result
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False, None
    except Exception as e:
        print(f"❌ 函数调用失败: {e}")
        traceback.print_exc()
        return False, None

def test_function_completeness(result):
    """测试函数完整性"""
    
    print("\n🔧 步骤2: 函数完整性测试...")
    
    if not result:
        print("❌ 没有有效的结果进行完整性测试")
        return False
    
    # 期望的键
    expected_keys = [
        'service_available',
        'mongodb_status', 
        'tdx_api_status',
        'enhanced_fetcher_available',
        'fallback_available',
        'checked_at'
    ]
    
    print("📋 检查期望的键...")
    
    completeness_score = 0
    for key in expected_keys:
        if key in result:
            print(f"  ✅ {key}: {result[key]}")
            completeness_score += 1
        else:
            print(f"  ❌ 缺少键: {key}")
    
    # 检查额外的键
    extra_keys = set(result.keys()) - set(expected_keys)
    if extra_keys:
        print(f"  ➕ 额外的键: {list(extra_keys)}")
    
    print(f"\n📊 完整性评分: {completeness_score}/{len(expected_keys)} ({(completeness_score/len(expected_keys)*100):.1f}%)")
    
    return completeness_score >= len(expected_keys) * 0.8  # 80%以上算通过

def test_function_values(result):
    """测试函数返回值的合理性"""
    
    print("\n🔧 步骤3: 返回值合理性测试...")
    
    if not result:
        print("❌ 没有有效的结果进行值测试")
        return False
    
    validation_results = []
    
    # 1. service_available 检查
    service_available = result.get('service_available')
    if isinstance(service_available, bool):
        print(f"  ✅ service_available: {service_available} (布尔值)")
        validation_results.append(True)
    else:
        print(f"  ❌ service_available 应该是布尔值: {service_available}")
        validation_results.append(False)
    
    # 2. mongodb_status 检查
    mongodb_status = result.get('mongodb_status')
    valid_mongodb_statuses = ['connected', 'disconnected', 'error']
    if mongodb_status in valid_mongodb_statuses:
        print(f"  ✅ mongodb_status: {mongodb_status} (有效状态)")
        validation_results.append(True)
    else:
        print(f"  ⚠️ mongodb_status: {mongodb_status} (可能的值: {valid_mongodb_statuses})")
        validation_results.append(False)
    
    # 3. tdx_api_status 检查
    tdx_status = result.get('tdx_api_status')
    valid_tdx_statuses = ['available', 'unavailable', 'limited', 'error']
    if tdx_status in valid_tdx_statuses:
        print(f"  ✅ tdx_api_status: {tdx_status} (有效状态)")
        validation_results.append(True)
    else:
        print(f"  ⚠️ tdx_api_status: {tdx_status} (可能的值: {valid_tdx_statuses})")
        validation_results.append(False)
    
    # 4. enhanced_fetcher_available 检查
    enhanced_available = result.get('enhanced_fetcher_available')
    if isinstance(enhanced_available, bool):
        print(f"  ✅ enhanced_fetcher_available: {enhanced_available} (布尔值)")
        validation_results.append(True)
    else:
        print(f"  ❌ enhanced_fetcher_available 应该是布尔值: {enhanced_available}")
        validation_results.append(False)
    
    # 5. fallback_available 检查
    fallback_available = result.get('fallback_available')
    if isinstance(fallback_available, bool):
        print(f"  ✅ fallback_available: {fallback_available} (布尔值)")
        validation_results.append(True)
    else:
        print(f"  ❌ fallback_available 应该是布尔值: {fallback_available}")
        validation_results.append(False)
    
    # 6. checked_at 检查
    checked_at = result.get('checked_at')
    if checked_at and isinstance(checked_at, str):
        try:
            from datetime import datetime
            datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
            print(f"  ✅ checked_at: {checked_at} (有效ISO时间格式)")
            validation_results.append(True)
        except ValueError:
            print(f"  ❌ checked_at 不是有效的ISO时间格式: {checked_at}")
            validation_results.append(False)
    else:
        print(f"  ❌ checked_at 应该是字符串: {checked_at}")
        validation_results.append(False)
    
    valid_count = sum(validation_results)
    total_count = len(validation_results)
    print(f"\n📊 值验证评分: {valid_count}/{total_count} ({(valid_count/total_count*100):.1f}%)")
    
    return valid_count >= total_count * 0.8

def test_function_performance():
    """测试函数性能"""
    
    print("\n🔧 步骤4: 性能测试...")
    
    try:
        from tradingagents.api.stock_api import check_service_status
        import time
        
        # 多次调用测试
        times = []
        results = []
        
        for i in range(3):
            print(f"  第{i+1}次调用...")
            start_time = time.time()
            result = check_service_status()
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            results.append(result)
            
            print(f"    用时: {duration:.3f}秒")
        
        # 性能统计
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n📊 性能统计:")
        print(f"  平均用时: {avg_time:.3f}秒")
        print(f"  最长用时: {max_time:.3f}秒")
        print(f"  最短用时: {min_time:.3f}秒")
        
        # 性能评级
        if avg_time < 1.0:
            print("  🚀 性能评级: 优秀 (< 1秒)")
            perf_score = 3
        elif avg_time < 3.0:
            print("  ⚡ 性能评级: 良好 (< 3秒)")
            perf_score = 2
        elif avg_time < 10.0:
            print("  ⏳ 性能评级: 一般 (< 10秒)")
            perf_score = 1
        else:
            print("  🐌 性能评级: 需要优化 (> 10秒)")
            perf_score = 0
        
        # 一致性检查
        consistent = all(r.get('service_available') == results[0].get('service_available') for r in results)
        if consistent:
            print("  ✅ 多次调用结果一致")
        else:
            print("  ⚠️ 多次调用结果不一致")
        
        return perf_score >= 1, avg_time
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False, None

def test_function_edge_cases():
    """测试边界情况"""
    
    print("\n🔧 步骤5: 边界情况测试...")
    
    try:
        from tradingagents.api.stock_api import check_service_status
        
        # 测试在不同条件下的行为
        print("  测试1: 正常调用...")
        result1 = check_service_status()
        if result1:
            print("    ✅ 正常调用成功")
        else:
            print("    ❌ 正常调用失败")
        
        # 测试连续调用
        print("  测试2: 连续快速调用...")
        for i in range(3):
            result = check_service_status()
            if result:
                print(f"    ✅ 第{i+1}次快速调用成功")
            else:
                print(f"    ❌ 第{i+1}次快速调用失败")
        
        print("  ✅ 边界情况测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 边界情况测试失败: {e}")
        return False

def analyze_service_status(result):
    """分析服务状态并给出建议"""
    
    print("\n🔧 步骤6: 服务状态分析...")
    
    if not result:
        print("❌ 没有有效的结果进行分析")
        return
    
    print("📋 服务状态分析报告:")
    print("-" * 50)
    
    # 总体服务可用性
    service_available = result.get('service_available', False)
    if service_available:
        print("  🟢 总体服务状态: 可用")
    else:
        print("  🔴 总体服务状态: 不可用")
        print("    💡 建议: 检查服务配置和依赖")
    
    # MongoDB状态分析
    mongodb_status = result.get('mongodb_status', 'unknown')
    if mongodb_status == 'connected':
        print("  🟢 MongoDB状态: 已连接 - 缓存功能正常")
    elif mongodb_status == 'disconnected':
        print("  🟡 MongoDB状态: 未连接 - 将使用文件缓存或直接API")
    elif mongodb_status == 'error':
        print("  🔴 MongoDB状态: 错误 - 请检查数据库配置")
        print("    💡 建议: 检查MongoDB连接字符串和权限")
    
    # 通达信API状态分析
    tdx_status = result.get('tdx_api_status', 'unknown')
    if tdx_status == 'available':
        print("  🟢 通达信API状态: 可用 - 可获取实时数据")
    elif tdx_status == 'limited':
        print("  🟡 通达信API状态: 有限 - 功能受限但基本可用")
    elif tdx_status == 'unavailable':
        print("  🔴 通达信API状态: 不可用 - 无法获取实时数据")
        print("    💡 建议: 检查网络连接和通达信服务器状态")
    elif tdx_status == 'error':
        print("  🔴 通达信API状态: 错误 - API调用失败")
        print("    💡 建议: 检查pytdx库安装和网络连接")
    
    # 增强功能分析
    enhanced_available = result.get('enhanced_fetcher_available', False)
    if enhanced_available:
        print("  🟢 增强获取器: 可用 - 支持高级功能")
    else:
        print("  🟡 增强获取器: 不可用 - 仅基础功能")
    
    # 降级机制分析
    fallback_available = result.get('fallback_available', False)
    if fallback_available:
        print("  🟢 降级机制: 可用 - 系统具备容错能力")
    else:
        print("  🔴 降级机制: 不可用 - 系统可靠性较低")
    
    print("-" * 50)
    
    # 综合建议
    print("\n💡 综合建议:")
    if service_available and (mongodb_status == 'connected' or tdx_status in ['available', 'limited']):
        print("  🎉 系统状态良好，可以正常使用所有功能")
    elif service_available:
        print("  ⚠️ 系统基本可用，但某些功能可能受限")
        print("  📝 建议优先修复数据库连接或API连接问题")
    else:
        print("  ❌ 系统不可用，需要立即修复")
        print("  🔧 请检查所有依赖项的安装和配置")

if __name__ == '__main__':
    print("开始全面测试 check_service_status() 函数...")
    
    # 测试计分
    scores = []
    
    # 1. 基础功能测试
    basic_ok, result = test_function_basic()
    scores.append(basic_ok)
    
    if basic_ok:
        # 2. 完整性测试
        completeness_ok = test_function_completeness(result)
        scores.append(completeness_ok)
        
        # 3. 返回值测试
        values_ok = test_function_values(result)
        scores.append(values_ok)
        
        # 4. 性能测试
        perf_ok, avg_time = test_function_performance()
        scores.append(perf_ok)
        
        # 5. 边界情况测试
        edge_ok = test_edge_cases()
        scores.append(edge_ok)
        
        # 6. 服务状态分析
        analyze_service_status(result)
        
    else:
        print("❌ 基础功能测试失败，跳过其他测试")
    
    # 总结
    print("\n" + "="*70)
    print("🎯 测试总结")
    print("="*70)
    
    if scores:
        success_count = sum(scores)
        total_count = len(scores)
        success_rate = (success_count / total_count) * 100
        
        print(f"测试通过率: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 check_service_status() 函数工作优秀!")
            print("✅ 函数完全可用，所有功能正常")
        elif success_rate >= 60:
            print("✅ check_service_status() 函数基本可用")
            print("⚠️ 有少量问题需要改进")
        elif success_rate >= 40:
            print("⚠️ check_service_status() 函数部分可用")
            print("🔧 需要修复一些关键问题")
        else:
            print("❌ check_service_status() 函数存在严重问题")
            print("🚨 需要全面检查和修复")
    else:
        print("❌ 无法进行完整测试 - 基础功能失败")
    
    print(f"\n测试完成时间: {datetime.now()}")
    
    if basic_ok and result:
        print(f"\n📋 最终状态摘要:")
        key_statuses = ['service_available', 'mongodb_status', 'tdx_api_status']
        for key in key_statuses:
            if key in result:
                print(f"  {key}: {result[key]}")