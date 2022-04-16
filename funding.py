""" calculate necessary funding based on heroku costs and s3 costs plus market size & business model """ 

from audioop import avg


S3_GET_COST = 0.0000004 # per request
S3_PUT_COST = 0.000005 # per request
YEARLY_MULTIVIEW_PAGE_LOADS = 260
ONE_GB_STORAGE_COST_PER_MONTH = 0.023
ONE_GB_STORAGE_COST_PER_YEAR = ONE_GB_STORAGE_COST_PER_MONTH * 12
YEARLY_HEROKU_COST = 6000 # dollars 

# What polydoc will charge
YEARLY_CHARGE_PER_STUDENT = 5.20 # dollars 
# estimated size of an average assignment (document) 
# including images for each page 
# (stored in S3)
avg_doc_size_range = range(1, 8) # MB 

# how many assignments per student per year ? 
assignments_per_student_per_year = range(50, 110, 10)

# estimated student to teacher ratio range
stu_teach_ratio_range = range(15, 105, 5) # 15 students per teacher up to 30 students per teacher



# targeting our first district with n students 
district_size_targets = range(1200, 2300, 100)

# how many requests will each teacher make against S3 in a year? 
# number of assignments they assign in a year * num students (PUT/POST) 
# plus
# number of assignments they assign in a year * num students * 260 work days (multiview page load) 
import os
def clear_log_files():
    for fname in ['net-gain','net-loss']:
        path = f'finances/{fname}.csv'
        if os.path.exists(path):
            os.remove(path)
def init(): 
    if not os.path.exists('finances'): 
        os.mkdir('finances')
    clear_log_files()

def log_year_situation(year_class='loss', data=None):
    """ log a year gain or loss situation where money is lost or profit is made due to diff in yearly cost vs yearly gain """
    with open(f'finances/net-{year_class}.csv', 'a') as f:
        line = ""
        num_keys = len(data.keys())
        for i, k in enumerate(data.keys()): 
            line += f'{k}={data[k]}, '
            if i == num_keys - 1: 
                line += f'\n'
        f.write(line)

def calculate_s3_cost():
    init()
    min_yearly_s3_cost = 100000000
    max_yearly_s3_cost = 0
    min_msg = ""
    max_msg = ""
    breakeven_msgs = []
    for student_body_size in district_size_targets:
        # what we make 
        total_yearly_gain = YEARLY_CHARGE_PER_STUDENT * student_body_size
        
        # what we have to pay 
        for stu_teach_ratio in stu_teach_ratio_range: 
            teacher_count = student_body_size / stu_teach_ratio 
            for aps in assignments_per_student_per_year:
                single_teacher_yearly_s3_get_requests_cost = aps * stu_teach_ratio * S3_GET_COST * YEARLY_MULTIVIEW_PAGE_LOADS
                single_teacher_yearly_s3_post_requests_cost = aps * stu_teach_ratio  * S3_PUT_COST 
                single_teacher_yearly_s3_requests_cost = single_teacher_yearly_s3_get_requests_cost + single_teacher_yearly_s3_post_requests_cost 
                all_teachers_yearly_s3_requests_cost = single_teacher_yearly_s3_requests_cost * teacher_count
                

                # Storage costs
                # assignments per student * num students * avg doc size (5MB)
                for docsize in avg_doc_size_range:
                    single_teacher_storage_use_per_year = aps * stu_teach_ratio * docsize
                    all_teachers_yearly_s3_storage_mb = single_teacher_storage_use_per_year * teacher_count
                    # new 
                    all_teachers_yearly_s3_storage_cost = (all_teachers_yearly_s3_storage_mb / 1000) * ONE_GB_STORAGE_COST_PER_YEAR
                    
                    total_yearly_s3_cost = all_teachers_yearly_s3_storage_cost + all_teachers_yearly_s3_requests_cost
                    
                    total_yearly_cost = YEARLY_HEROKU_COST + total_yearly_s3_cost

                    s3_msg = (
                        f'S3 COSTS FOR 1 year: \n'
                        f'\tSTORAGE: ${all_teachers_yearly_s3_storage_cost}\n'
                        f'\tREQUESTS: ${all_teachers_yearly_s3_requests_cost}\n'
                        f'\tS3 Total: ${total_yearly_s3_cost}\n'
                        f'\t({teacher_count} teachers, \n'
                        f'\t{stu_teach_ratio} students per teacher,\n'
                        f'\t{aps} assignments per student per year)\n'
                        f'\t{docsize}MB avg doc size per assignment\n\n'
                    ) 

                    data = {
                        'teacher_count': teacher_count, 
                        'student_teacher_ratio': stu_teach_ratio,
                        'assignments_per_stu_per_year': aps, 
                        'avg_doc_size': docsize,
                        's3_storage_year_cost': all_teachers_yearly_s3_storage_cost,
                        's3_requests_year_cost': all_teachers_yearly_s3_requests_cost,
                        's3_year_cost': total_yearly_s3_cost,
                        'heroku_year_cost': YEARLY_HEROKU_COST, 
                        'total_yearly_cost': total_yearly_cost, 
                        'total_yearly_gain': total_yearly_gain
                    }
                    
                    log_year_situation(
                        year_class='gain' if total_yearly_cost <= total_yearly_gain else 'loss',
                        data=data
                    )
                        
                    if total_yearly_s3_cost < min_yearly_s3_cost: 
                        min_yearly_s3_cost = total_yearly_s3_cost
                        min_msg = s3_msg
                    if total_yearly_s3_cost > max_yearly_s3_cost:
                        max_yearly_s3_cost = total_yearly_s3_cost
                        max_msg = s3_msg
        print("MIN")
        print(min_msg)
        print("MAX")
        print(max_msg)
        print(breakeven_msgs)
        return min_yearly_s3_cost, max_yearly_s3_cost

if __name__ == "__main__": 
    calculate_s3_cost()