def get_rating_stats(product):
    total = product.total_people_rated or 1
    return {
        'rating_percentages': {
            '5': round((product.rating_5_count / total) * 100, 1),
            '4': round((product.rating_4_count / total) * 100, 1),
            '3': round((product.rating_3_count / total) * 100, 1),
            '2': round((product.rating_2_count / total) * 100, 1),
            '1': round((product.rating_1_count / total) * 100, 1),
        }
    }