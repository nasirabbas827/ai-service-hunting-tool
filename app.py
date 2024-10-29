from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import io
import base64
import time
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'extractor_db'

mysql = MySQL(app)


# Ensure necessary NLTK resources are available
nltk.download('punkt')
nltk.download('stopwords')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Hash the password for security

        # Check if the username is already taken
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cur.fetchone()
        cur.close()

        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

        # Insert user into the database
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users (name, username, password) VALUES (%s, %s, %s)',
                    (name, username, password))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('user_login'))

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists in the database
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):  # Check if password matches
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful. Welcome, {}!'.format(user[1]), 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('user_login'))

    return render_template('user_login.html')



import requests
from bs4 import BeautifulSoup

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session:
        flash('You must login first.', 'error')
        return redirect(url_for('user_login'))

    # Fetch feedbacks from the database
    feedbacks = get_feedbacks()


    return render_template('user_dashboard.html', feedbacks=feedbacks)

def get_feedbacks():
    # Function to retrieve all feedbacks from the database
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT feedback.feedback_message, feedback.rating, users.username 
        FROM feedback 
        JOIN users ON feedback.user_id = users.user_id
    ''')
    feedbacks = cur.fetchall()  # Fetch all feedback records
    cur.close()
    
    # Convert feedback records to a list of dictionaries for easier access in the template
    return [{'message': feedback[0], 'rating': feedback[1], 'username': feedback[2]} for feedback in feedbacks]


@app.route('/user_logout')
def user_logout():
    # Remove user_id from the session upon logout
    session.pop('user_id', None)
    # Redirect to the login page after logging out
    return redirect(url_for('user_login'))




# Function to scrape Fiverr gigs
def scrape_fiverr(skill):
    base_url = f'https://www.fiverr.com/categories/programming-tech/buy/website-development/landing-page?source=category_tree&query={skill.replace(" ", "%20")}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        return [], []  # Return empty lists if the request fails

    soup = BeautifulSoup(response.content, 'html.parser')
    gig_cards = soup.find_all('div', class_='basic-gig-card')
    gigs = []
    ratings_set = set()  # For storing unique ratings

    for gig in gig_cards[:5]:  # Limit to top 5 results
        title = gig.find('p', {'role': 'heading', 'aria-level': '3'})
        url = 'https://www.fiverr.com' + gig.find('a', {'aria-label': 'Go to gig'})['href'] if title else 'No URL'
        
        price = gig.find('span', class_='text-bold co-grey-1200')
        rating = gig.find('strong', class_='rating-score')
        rating_count = gig.find('span', class_='rating-count-number')
        country = gig.find('p', class_='z58z872')

        if rating:
            ratings_set.add(rating.text)  # Collect unique ratings for dropdown filter

        gigs.append({
            'title': title.text if title else 'No Title',
            'url': url,
            'price': price.text if price else 'No Price',
            'rating': rating.text if rating else 'No Rating',
            'rating_count': rating_count.text if rating_count else 'No Rating Count',
            'country': country.text if country else 'No Country'
        })

    return gigs, sorted(ratings_set)

# Function to extract keywords from each gig's description
def extract_keywords_from_gigs(gigs):
    all_keywords = []
    for gig in gigs:
        gig_details = get_description(gig['url'])
        if gig_details:
            all_keywords.extend(gig_details['keywords'])  # Collect keywords from each gig
    return list(set(all_keywords))  # Return unique keywords

# Route to display results and keyword analysis button with rating filter
@app.route('/results')
def results():
    gigs, ratings_set = session.get('gigs', ([], []))
    min_rating = request.args.get('min_rating')
    if min_rating:
        gigs = [gig for gig in gigs if gig['rating'] == min_rating]

    # Extract keywords from all gig descriptions
    all_keywords = extract_keywords_from_gigs(gigs)

    keywords = keyword_analysis(' '.join([gig['title'] for gig in gigs])) if gigs else []
    return render_template('results.html', gigs=gigs, keywords=all_keywords, ratings=ratings_set)

import re  # Ensure you have this import at the top of your file

@app.route('/visualize_stats')
def visualize_stats():
    gigs = session.get('gigs', ([], []))[0]  # Get gigs from session

    # Calculate total sales
    total_sales = 0.0
    for gig in gigs:
        price = gig['price']
        if price != 'No Price':
            # Use regex to find numeric values in the price string
            cleaned_price = re.findall(r'\d+', price)  # Find all digit sequences
            if cleaned_price:  # Check if there's any numeric part found
                total_sales += float(cleaned_price[0])  # Add the first found numeric part as float

    # Calculate average rating
    average_rating = sum(float(gig['rating']) for gig in gigs if gig['rating'] != 'No Rating') / len(gigs) if gigs else 0

    # Prepare data for plotting
    ratings = [float(gig['rating']) for gig in gigs if gig['rating'] != 'No Rating']
    plt.figure(figsize=(10, 6))
    plt.hist(ratings, bins=10, color='blue', alpha=0.7)
    plt.title('Distribution of Gig Ratings')
    plt.xlabel('Ratings')
    plt.ylabel('Frequency')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    # Render the stats page with the plot
    return render_template('visualization.html', total_sales=total_sales, average_rating=average_rating, plot_url=plot_url)


# Define keyword analysis function (simplified)
def keyword_analysis(text):
    tokens = nltk.word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    word_freq = Counter(tokens)
    return [word for word, freq in word_freq.most_common(10)]

# Route for search form on user_dashboard
@app.route('/search', methods=['POST'])
def search():
    skill = request.form['skill']
    gigs = scrape_fiverr(skill)
    session['gigs'] = gigs  # Store gigs in session to pass to the results page
    return redirect(url_for('results'))

# Route to view a specific gig with description and other details
@app.route('/view_gig')
def view_gig():
    gig_url = request.args.get('gig_url')
    gig_details = get_description(gig_url)
    if gig_details:
        return render_template('view_gig.html', gig=gig_details)
    else:
        flash("Failed to retrieve gig details.", "error")
        return redirect(url_for('results'))


def get_description(gig_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    try:
        response = requests.get(gig_url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

    if response.status_code != 200:
        print("Failed to retrieve page. Status code:", response.status_code)
        return None

    time.sleep(random.uniform(2, 5))  # To avoid being detected as a bot

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting details
    title = soup.find('h1', class_='text-display-3')
    title_text = title.text.strip() if title else 'No Title Available'

    price = soup.find('span', class_='o6KMeAI tbody-4 text-bold')
    price_text = price.text.strip() if price else 'No Price Available'

    rating = soup.find('strong', class_='rating-score')
    rating_text = rating.text.strip() if rating else 'No Rating Available'

    rating_count = soup.find('span', class_='ratings-count khO62BA')
    rating_count_text = rating_count.find('span', class_='rating-count-number').text if rating_count else 'No Ratings Count Available'

    description = soup.find('div', class_='description-content')
    description_text = description.text.strip() if description else 'No Description Available'

    user_stats = soup.find('ul', class_='user-stats')
    user_stats_list = user_stats.find_all('li') if user_stats else []
    user_stats_text = '<br>'.join([stat.text.strip() for stat in user_stats_list]) if user_stats_list else 'No User Stats Available'

    extra_divs = soup.find_all('div', class_='zle7n01ad zle7n00 zle7n010d zle7n018z zle7n01b2')
    extra_div_text = ' | '.join([div.text.strip() for div in extra_divs]) if extra_divs else 'No Additional Info Available'

    keywords = keyword_analysis(description_text)  # Analyze keywords from the description

    return {
        'title': title_text,
        'price': price_text,
        'rating': rating_text,
        'rating_count': rating_count_text,
        'description': description_text,
        'user_stats': user_stats_text,
        'additional_info': extra_div_text,
        'keywords': keywords,
        'url': gig_url
    }


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        flash('You must login first.', 'error')
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        # Retrieve form data
        user_id = session['user_id']
        feedback_message = request.form['feedback_message']
        rating = request.form['rating']

        # Insert feedback into the database
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO feedback (user_id, feedback_message, rating) VALUES (%s, %s, %s)',
                    (user_id, feedback_message, rating))
        mysql.connection.commit()
        cur.close()

        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('feedback'))

    return render_template('feedback.html')


if __name__ == '__main__':
    app.run(debug=True)