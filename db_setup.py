import datetime
import mysql.connector

DB_SERVER_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
}

DB_NAME = 'credirate'


def setup_db():
    server_conn = mysql.connector.connect(**DB_SERVER_CONFIG)
    server_cursor = server_conn.cursor()
    server_cursor.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
    server_cursor.close()
    server_conn.close()

    conn = mysql.connector.connect(database=DB_NAME, **DB_SERVER_CONFIG)
    c = conn.cursor()

    c.execute('DROP VIEW IF EXISTS vw_trust_scores')
    c.execute('DROP VIEW IF EXISTS vw_credibility_weights')
    c.execute('DROP TABLE IF EXISTS entity_feedback')
    c.execute('DROP TABLE IF EXISTS ratings')
    c.execute('DROP TABLE IF EXISTS entities')
    c.execute('DROP TABLE IF EXISTS users')

    c.execute('''
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_verified BOOLEAN DEFAULT FALSE,
            reputation_score INT DEFAULT 50
        )
    ''')

    c.execute('''
        CREATE TABLE entities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            description TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE ratings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            entity_id INT NOT NULL,
            rating_value INT NOT NULL,
            review_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_rating_value CHECK (rating_value >= 1 AND rating_value <= 5),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE entity_feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            entity_id INT NOT NULL,
            user_name VARCHAR(100) NOT NULL,
            rating_value INT NOT NULL,
            feedback_text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_feedback_rating CHECK (rating_value >= 1 AND rating_value <= 5),
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE VIEW vw_credibility_weights AS
        SELECT
            r.id AS rating_id,
            r.user_id,
            r.entity_id,
            r.rating_value,
            r.review_text,
            r.created_at,
            u.username,
            u.is_verified,
            u.reputation_score,
            TIMESTAMPDIFF(DAY, r.created_at, NOW()) AS age_days,
            (
                SELECT COUNT(*)
                FROM ratings r_hist
                WHERE r_hist.user_id = r.user_id
            ) AS total_reviews_by_user,
            (
                SELECT COUNT(*)
                FROM ratings r_repeat
                WHERE r_repeat.user_id = r.user_id
                  AND r_repeat.entity_id = r.entity_id
                  AND r_repeat.id < r.id
            ) AS prior_reviews_for_entity,
            CASE
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 7 THEN 1.5
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 30 THEN 1.2
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 90 THEN 1.0
                ELSE 0.8
            END AS recency_factor,
            CASE
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 7 THEN 'Immediate'
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 30 THEN 'Recent'
                WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 90 THEN 'Standard'
                ELSE 'Stale'
            END AS recency_bucket,
            (u.reputation_score / 50.0) + (u.is_verified * 0.2) AS user_reliability_factor,
            (u.reputation_score / 50.0) AS reputation_factor,
            (u.is_verified * 0.2) AS verification_bonus,
            CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM ratings r_hist
                    WHERE r_hist.user_id = r.user_id
                ) >= 8 THEN 1.20
                WHEN (
                    SELECT COUNT(*)
                    FROM ratings r_hist
                    WHERE r_hist.user_id = r.user_id
                ) >= 4 THEN 1.10
                WHEN (
                    SELECT COUNT(*)
                    FROM ratings r_hist
                    WHERE r_hist.user_id = r.user_id
                ) >= 2 THEN 1.00
                ELSE 0.90
            END AS history_factor,
            CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM ratings r_repeat
                    WHERE r_repeat.user_id = r.user_id
                      AND r_repeat.entity_id = r.entity_id
                      AND r_repeat.id < r.id
                ) > 0 THEN 1.08
                ELSE 1.00
            END AS repeat_reviewer_factor,
            (
                CASE
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 7 THEN 1.5
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 30 THEN 1.2
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 90 THEN 1.0
                    ELSE 0.8
                END
            ) *
            ((u.reputation_score / 50.0) + (u.is_verified * 0.2)) *
            (
                CASE
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 8 THEN 1.20
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 4 THEN 1.10
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 2 THEN 1.00
                    ELSE 0.90
                END
            ) *
            (
                CASE
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_repeat
                        WHERE r_repeat.user_id = r.user_id
                          AND r_repeat.entity_id = r.entity_id
                          AND r_repeat.id < r.id
                    ) > 0 THEN 1.08
                    ELSE 1.00
                END
            ) AS final_weight,
            CONCAT(
                'Recency: ',
                CASE
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 7 THEN 'Immediate (<= 7 days, x1.5)'
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 30 THEN 'Recent (<= 30 days, x1.2)'
                    WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 90 THEN 'Standard (<= 90 days, x1.0)'
                    ELSE 'Stale (> 90 days, x0.8)'
                END,
                '; Reliability: reputation factor x', ROUND((u.reputation_score / 50.0), 2),
                CASE
                    WHEN u.is_verified = 1 THEN ' plus verified bonus +0.20'
                    ELSE ' with no verified bonus'
                END,
                '; History factor: x',
                CASE
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 8 THEN '1.20'
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 4 THEN '1.10'
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_hist
                        WHERE r_hist.user_id = r.user_id
                    ) >= 2 THEN '1.00'
                    ELSE '0.90'
                END,
                '; Repeat reviewer factor: x',
                CASE
                    WHEN (
                        SELECT COUNT(*)
                        FROM ratings r_repeat
                        WHERE r_repeat.user_id = r.user_id
                          AND r_repeat.entity_id = r.entity_id
                          AND r_repeat.id < r.id
                    ) > 0 THEN '1.08'
                    ELSE '1.00'
                END,
                '; Final weight: ',
                ROUND(
                    (
                        CASE
                            WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 7 THEN 1.5
                            WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 30 THEN 1.2
                            WHEN TIMESTAMPDIFF(DAY, r.created_at, NOW()) <= 90 THEN 1.0
                            ELSE 0.8
                        END
                    ) *
                    ((u.reputation_score / 50.0) + (u.is_verified * 0.2)) *
                    (
                        CASE
                            WHEN (
                                SELECT COUNT(*)
                                FROM ratings r_hist
                                WHERE r_hist.user_id = r.user_id
                            ) >= 8 THEN 1.20
                            WHEN (
                                SELECT COUNT(*)
                                FROM ratings r_hist
                                WHERE r_hist.user_id = r.user_id
                            ) >= 4 THEN 1.10
                            WHEN (
                                SELECT COUNT(*)
                                FROM ratings r_hist
                                WHERE r_hist.user_id = r.user_id
                            ) >= 2 THEN 1.00
                            ELSE 0.90
                        END
                    ) *
                    (
                        CASE
                            WHEN (
                                SELECT COUNT(*)
                                FROM ratings r_repeat
                                WHERE r_repeat.user_id = r.user_id
                                  AND r_repeat.entity_id = r.entity_id
                                  AND r_repeat.id < r.id
                            ) > 0 THEN 1.08
                            ELSE 1.00
                        END
                    ),
                    2
                )
            ) AS credibility_breakdown
        FROM ratings r
        JOIN users u ON r.user_id = u.id
    ''')

    c.execute('''
        CREATE VIEW vw_trust_scores AS
        SELECT
            e.id AS entity_id,
            e.name AS entity_name,
            e.description,
            COUNT(vw.rating_id) AS total_ratings,
            SUM(vw.rating_value * vw.final_weight) / NULLIF(SUM(vw.final_weight), 0) AS trust_score,
            AVG(vw.rating_value) AS simple_average
        FROM entities e
        LEFT JOIN vw_credibility_weights vw ON e.id = vw.entity_id
        GROUP BY e.id, e.name, e.description
    ''')

    users = [
        ('Priya Menon', 1, 92),
        ('Arjun Kapoor', 1, 78),
        ('Neha Singh', 0, 58),
        ('Rohan Das', 0, 32),
        ('Simran Kaur', 1, 85),
        ('Aditi Rao', 0, 44),
        ('Kabir Shah', 0, 64)
    ]
    c.executemany(
        'INSERT INTO users (username, is_verified, reputation_score) VALUES (%s, %s, %s)',
        users
    )

    entities = [
        ('Asteria Bistro', 'A contemporary dining destination known for curated seasonal menus.'),
        ('Nimbus Electronics', 'A consumer electronics retailer focused on smart devices and after-sales support.'),
        ('Northwind Health', 'A modern multi-specialty healthcare provider.'),
        ('BluePeak Fitness', 'A boutique gym focused on strength and wellness.'),
        ('Luma Stay Suites', 'A business-friendly hotel and short-stay brand.'),
        ('Crestline Bank', 'A regional banking service with digital-first support.')
    ]
    c.executemany(
        'INSERT INTO entities (name, description) VALUES (%s, %s)',
        entities
    )

    conn.commit()

    c.execute('SELECT id, username FROM users')
    user_ids = {username: user_id for user_id, username in c.fetchall()}

    c.execute('SELECT id, name FROM entities')
    entity_ids = {name: entity_id for entity_id, name in c.fetchall()}

    now = datetime.datetime.now()

    def days_ago(days, hour=10, minute=0):
        return (now - datetime.timedelta(days=days)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

    seeded_reviews = [
        ('Priya Menon', 'Asteria Bistro', 5, 'Exceptional tasting menu and polished service throughout the evening.', days_ago(3, 20, 15)),
        ('Priya Menon', 'Nimbus Electronics', 4, 'Reliable product guidance and a smooth exchange process.', days_ago(12, 14, 20)),
        ('Priya Menon', 'Northwind Health', 5, 'Specialists were organised, transparent, and very reassuring.', days_ago(22, 9, 30)),
        ('Priya Menon', 'BluePeak Fitness', 4, 'Coaches are attentive and the strength programs feel thoughtfully planned.', days_ago(31, 18, 10)),
        ('Priya Menon', 'Crestline Bank', 4, 'Loan support was quick and the digital onboarding was simple.', days_ago(48, 11, 5)),
        ('Arjun Kapoor', 'Asteria Bistro', 4, 'Strong food quality, though the dessert course felt a little rushed.', days_ago(6, 21, 10)),
        ('Arjun Kapoor', 'Nimbus Electronics', 5, 'Demo staff explained the device ecosystem really well.', days_ago(9, 13, 45)),
        ('Arjun Kapoor', 'BluePeak Fitness', 3, 'Solid equipment, but peak-hour crowding can be distracting.', days_ago(19, 19, 0)),
        ('Neha Singh', 'Asteria Bistro', 4, 'Loved the ambience and the chef interaction at the counter.', days_ago(2, 20, 45)),
        ('Neha Singh', 'Northwind Health', 3, 'Good doctors, but the waiting time at reception was noticeable.', days_ago(16, 12, 15)),
        ('Rohan Das', 'Asteria Bistro', 2, 'Felt overpriced for the portion size I received.', days_ago(1, 22, 0)),
        ('Simran Kaur', 'Asteria Bistro', 5, 'Second visit was even better than the first and the service team remembered preferences.', days_ago(4, 20, 50)),
        ('Simran Kaur', 'Asteria Bistro', 5, 'Came back for a client dinner and the consistency was impressive.', days_ago(0, 19, 5)),
        ('Simran Kaur', 'Luma Stay Suites', 4, 'Rooms were quiet, clean, and ideal for a short work trip.', days_ago(11, 8, 35)),
        ('Simran Kaur', 'Crestline Bank', 5, 'Relationship manager handled the request professionally and fast.', days_ago(28, 15, 0)),
        ('Aditi Rao', 'BluePeak Fitness', 2, 'Trainers were friendly but the beginner onboarding felt weak.', days_ago(5, 17, 20)),
        ('Kabir Shah', 'Nimbus Electronics', 4, 'Pickup was quick and warranty terms were explained clearly.', days_ago(7, 16, 25)),
        ('Kabir Shah', 'BluePeak Fitness', 5, 'Great coaching energy and clean workout zones.', days_ago(3, 18, 40)),
    ]

    for username, entity_name, stars, review_text, created_at in seeded_reviews:
        user_id = user_ids[username]
        entity_id = entity_ids[entity_name]
        c.execute(
            '''
            INSERT INTO ratings (user_id, entity_id, rating_value, review_text, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ''',
            (user_id, entity_id, stars, review_text, created_at)
        )
        c.execute(
            '''
            INSERT INTO entity_feedback (entity_id, user_name, rating_value, feedback_text, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ''',
            (entity_id, username, stars, review_text, created_at)
        )

    conn.commit()
    c.close()
    conn.close()
    print('MySQL database reset and seeded with professor-demo data.')


if __name__ == '__main__':
    setup_db()
