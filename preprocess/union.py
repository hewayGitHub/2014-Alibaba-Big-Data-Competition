__author__ = 'heway'

def union_rec(pre_rec_filename, rec_filename):
    """
    union different recommend result
    """
    pre_rec_purchase = dict()
    pre_count = 0
    with open('out/' + pre_rec_filename) as pre_rec_file:
        for line in pre_rec_file:
            items = line.strip().split('\t')
            if len(items) != 2:
                continue

            user_id = items[0]
            pre_rec_purchase.setdefault(user_id, set())

            brand_ids = items[1].split(',')
            for brand_id in brand_ids:
                pre_count += 1
                pre_rec_purchase[user_id].add(brand_id)

    print 'Num of pre_rec:', pre_count

    rec_purchase = dict()
    count = 0
    with open('out/' + rec_filename) as rec_file:
        for line in rec_file:
            items = line.strip().split('\t')
            if len(items) != 2:
                continue

            user_id = items[0]
            rec_purchase.setdefault(user_id, set())

            brand_ids = items[1].split(',')
            for brand_id in brand_ids:
                count += 1
                rec_purchase[user_id].add(brand_id)

    print 'Num of rec:', count

    common_count = 0
    for user_id, brand_ids in pre_rec_purchase.items():
        if user_id in rec_purchase:
            for brand_id in brand_ids:
                if brand_id in rec_purchase[user_id]:
                    common_count += 1
    print 'Common:', common_count

    add_count = 0
    for user_id, brand_ids in pre_rec_purchase.items():
        if user_id in rec_purchase:
            for brand_id in brand_ids:
                if brand_id not in rec_purchase[user_id]:
                    add_count += 1
                    rec_purchase[user_id].add(brand_id)
        else:
            rec_purchase[user_id] = brand_ids
            add_count += len(brand_ids)

    print 'add:', add_count
    print pre_count + count - common_count, count + add_count

    with open('out/union.txt', 'w') as union_file:
        for user_id, brand_ids in rec_purchase.items():
            union_file.write(user_id + '\t' + ','.join(brand_ids) + '\n')

def intersect_all(filenames):
    """
    intersect different recommend result
    """
    intersect = dict()
    is_first = True
    count = 0
    for filename in filenames:
        with open('out/' + filename) as rec_file:
            for line in rec_file:
                items = line.strip().split('\t')
                if len(items) != 2:
                    continue

                user_id = items[0]
                intersect.setdefault(user_id, set())

                brand_ids = items[1].split(',')
                if is_first:
                    for brand_id in brand_ids:
                        intersect[user_id].add(brand_id)
                        count += 1
                else:
                    if user_id in intersect:
                        count -= len(intersect[user_id])
                        intersect[user_id] &= set(brand_ids)
                        count += len(intersect[user_id])

        print count
        is_first = False

    intersect_file = open('out/intersect.txt', 'w')
    for user_id, brand_ids in intersect.items():
        if len(brand_ids) == 0:
            continue
        intersect_file.write(user_id + '\t' + ','.join(brand_ids) + '\n')

    print 'Common:', count

    intersect_file.close()

def union_all(filenames):
    """
    intersect different recommend result
    """
    union = dict()
    count = 0
    for filename in filenames:
        with open('out/' + filename) as rec_file:
            for line in rec_file:
                items = line.strip().split('\t')
                if len(items) != 2:
                    continue

                user_id = items[0]
                union.setdefault(user_id, set())

                brand_ids = items[1].split(',')
                for brand_id in brand_ids:
                    if brand_id not in union[user_id]:
                        union[user_id].add(brand_id)
                        count += 1

    union_file = open('out/union.txt', 'w')
    for user_id, brand_ids in union.items():
        if len(brand_ids) == 0:
            continue
        union_file.write(user_id + '\t' + ','.join(brand_ids) + '\n')

    print 'Sum:', count

    union_file.close()

if __name__ == '__main__':
    #intersect_all(['6.83.txt', '7.06.txt'])
    #union_all(['6.83.txt', '7.06.txt'])
    union_all(['rec.txt', 'rec_lr.txt'])
