import random
import json
from tools import modify_params, exe_pyswmm_all, calculate_errors, process_excel_files

# 加载数据和节点信息
data_dict = process_excel_files('data1')
# node_dict = exe_pyswmm_all("Optimization Algorithm.inp")

# 定义数据和节点
datas = [
    data_dict['JHHN2'],
    data_dict['东城河污水处理厂'],
    data_dict['界洪河新阳路'],
    data_dict['东城河铁路南'],
    data_dict['界亳河汪庄'],
    data_dict['幸福沟']
]

# nodes = [
#     node_dict['DCH-W-P2'],
#     node_dict['JHHN4'],
#     node_dict["JHHN2"],
#     node_dict["DCH-W-P2"],
#     node_dict["JBH-N-P3"],
#     node_dict["XFG-N-P5"]
# ]
for data in datas:
    data["平均流量（m³/s）"] = data["平均流量（m³/5min）"]/300

# 定义参数范围
param_ranges = {
    'param1': (20, 90),
    'param2': (0, 10),
    'param3': (2, 7),
    'n_imperv': (0.005, 0.05),
    'n_perv': (0.05, 0.5),
    's_imperv': (0.2, 10),
    's_perv': (2, 10)
}


# 初始化种群
def initialize_population(pop_size):
    population = [{
            'param1': 20,
            'param2': 0,
            'param3': 4,
            'n_imperv': 0.03,
            'n_perv': 0.3,
            's_imperv': 2,
            's_perv': 6
        }]
    for _ in range(pop_size-1):
        individual = {
            'param1': random.uniform(*param_ranges['param1']),
            'param2': random.uniform(*param_ranges['param2']),
            'param3': random.uniform(*param_ranges['param3']),
            'n_imperv': random.uniform(*param_ranges['n_imperv']),
            'n_perv': random.uniform(*param_ranges['n_perv']),
            's_imperv': random.uniform(*param_ranges['s_imperv']),
            's_perv': random.uniform(*param_ranges['s_perv'])
        }
        population.append(individual)
    return population


# 评估种群
def evaluate_population(population):
    errors = []
    for individual in population:
        # 修改输入文件
        modify_params(
            "Optimization Algorithm.inp",
            individual['param1'],
            individual['param2'],
            individual['param3'],
            individual['n_imperv'],
            individual['n_perv'],
            individual['s_imperv'],
            individual['s_perv']
        )

        # 重新运行模型
        node_dict = exe_pyswmm_all("Optimization Algorithm.inp")
        nodes = [
            node_dict["JHHN2"],
            # node_dict['DCH-W-P2'],
            # node_dict['JHHN4'],
            # node_dict["DCH-W-P2"],
            # node_dict["JBH-N-P3"],
            # node_dict["XFG-N-P5"]
        ]
        # 计算误差
        total_error = 0
        for i, node in enumerate(nodes):
            error_value = -1 * calculate_errors(node, datas[i],error_type='nse')  # 纳什效率系数
            total_error += error_value
        errors.append(total_error)
    return errors


# 选择操作
def selection(population, errors, num_parents):
    sorted_indices = sorted(range(len(errors)), key=lambda k: errors[k])
    selected_indices = sorted_indices[:num_parents]
    selected_population = [population[i] for i in selected_indices]
    return selected_population


# 交叉操作
def crossover(parents, offspring_size):
    offspring = []
    for _ in range(offspring_size):
        parent1, parent2 = random.sample(parents, 2)
        child = {}
        for key in parent1.keys():
            if random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        offspring.append(child)
    return offspring


# 变异操作
def mutation(offspring, mutation_rate=0.1):
    for individual in offspring:
        for key in individual.keys():
            if random.random() < mutation_rate:
                individual[key] = random.uniform(*param_ranges[key])
    return offspring


# 遗传算法主函数
def genetic_algorithm(pop_size=50, num_generations=80, num_parents=20, mutation_rate=0.1):
    population = initialize_population(pop_size)
    # 创建一个字典来存储每代的误差信息
    error_log = {"generations": []}
    for generation in range(num_generations):
        errors = evaluate_population(population)
        parents = selection(population, errors, num_parents)
        offspring = crossover(parents, pop_size - num_parents)
        offspring = mutation(offspring, mutation_rate)
        population = parents + offspring
        # 记录当前代的误差信息
        generation_info = {
            "generation": generation + 1,
            "best_error": min(errors),
            "average_error": sum(errors) / len(errors),
            "errors": errors
        }
        error_log["generations"].append(generation_info)
        print(f"Generation {generation + 1}, Best Error: {min(errors):.4f}")
    # 将误差记录保存为JSON文件
    with open("error_log_all_modified.json", "w") as json_file:
        json.dump(error_log, json_file, indent=4)
    # 返回最优解
    best_index = errors.index(min(errors))
    return population[best_index]


# 运行遗传算法
best_solution = genetic_algorithm()
print("Best Solution:", best_solution)

# 使用最优解更新输入文件
modify_params(
    "Optimization Algorithm.inp",
    best_solution['param1'],
    best_solution['param2'],
    best_solution['param3'],
    best_solution['n_imperv'],
    best_solution['n_perv'],
    best_solution['s_imperv'],
    best_solution['s_perv']
)