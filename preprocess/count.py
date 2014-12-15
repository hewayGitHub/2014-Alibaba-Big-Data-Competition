__author__ = 'heway'


def count_common(last_day=91, filename='rec.txt'):
    """
    Compare 'out/rec.txt' and purchases that happen after the last day
    Summarize how many are in common
    """
    pre_purchase = set()
    test_purchase = set()
    with open('in/t_alibaba_data.csv_sorted') as test_file:
        for line in test_file:
            items = line.strip().split(',')
            if len(items) != 4:
                continue

            user_id = items[0]
            brand_id = items[1]
            act = items[2]
            date = int(items[3])

            if act == '5':
                if date > last_day:
                    test_purchase.add(user_id + '^' + brand_id)
                else:
                    pre_purchase.add(user_id + '^' + brand_id)

    print 'Sum of purchases:', len(test_purchase)

    rec_purchase = set()
    with open('out/' + filename) as rec_file:
        for line in rec_file:
            items = line.strip().split('\t')
            if len(items) != 2:
                continue

            user_id = items[0]
            brand_ids = items[1].split(',')
            for brand_id in brand_ids:
                rec_purchase.add(user_id + '^' + brand_id)

    print 'Num of rec:', len(rec_purchase)

    hit = 0
    hit_purchase = set()
    for key in rec_purchase:
        if key in test_purchase:
            hit += 1
            hit_purchase.add(key)
        else:
            pass
            #print key
    print 'Common:', hit
    if len(test_purchase) != 0:
        precision = hit * 1.0 / len(rec_purchase)
        recall = hit * 1.0 / len(test_purchase)
        print precision, recall, 2 * precision * recall / (precision + recall)

    has_purchase_count = 0
    for key in hit_purchase:
        if key in pre_purchase:
            has_purchase_count += 1
        else:
            pass
            #print key
    print 'pre_purchase:', has_purchase_count

    top_hit = dict()
    top = 0
    hit = 0
    with open('out/rec_count.txt') as rec_file:
        for line in rec_file:
            key = line.strip()
            top += 1

            if key in test_purchase:
                hit += 1

            top_hit[top] = hit

    for top, hit in top_hit.items():
        if top != hit:
            print 'difference happen in:', top
            break

    if last_day != -1:
        print '------------has purchased'
        count_common(last_day=-1, filename=filename)

def count_out_common():
    """
    Compare 'out/rec.txt' and purchases that happen after the last day
    Summarize how many are in common
    """
    pre_rec_purchase = set()
    with open('out/6.59.txt') as rec_file:
        for line in rec_file:
            items = line.strip().split('\t')
            if len(items) != 2:
                continue

            user_id = items[0]
            brand_ids = items[1].split(',')
            for brand_id in brand_ids:
                pre_rec_purchase.add(user_id + '^' + brand_id)

    print 'Num of pre_rec:', len(pre_rec_purchase)

    rec_purchase = set()
    with open('out/rec.txt') as rec_file:
        for line in rec_file:
            items = line.strip().split('\t')
            if len(items) != 2:
                continue

            user_id = items[0]
            brand_ids = items[1].split(',')
            for brand_id in brand_ids:
                rec_purchase.add(user_id + '^' + brand_id)

    print 'Num of rec:', len(rec_purchase)

    hit = 0
    for key in rec_purchase:
        if key in pre_rec_purchase:
            hit += 1
        else:
            pass
            #print key
    print 'Common:', hit

if __name__ == '__main__':
    #count recomend how many purchased
    count_common(last_day=-1, filename='7.06.txt')
    #count_out_common()