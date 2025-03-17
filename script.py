import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
import seaborn as sns
import re
from scipy.stats import chi2_contingency
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
from nltk.corpus import stopwords
from collections import Counter
######################### data importing and data cleaning #########################

new_articles=pd.read_csv(r'C:\\Users\tzwrakos\\OneDrive\\Υπολογιστής\\Projects\\Fake News Detection Udemy\\dataset\\news_articles.csv')
new_articles.dropna(axis=0,inplace=True)
new_articles.drop_duplicates(inplace=True)
cleaned_dataset=pd.read_csv(r'C:\\Users\\tzwrakos\\OneDrive\\Υπολογιστής\\Projects\\Fake News Detection Udemy\\dataset\\cleaned_dataset.csv')

######################### new source credibility analysis #########################

source_counts=cleaned_dataset.groupby(["site_url","label"]).size().unstack(fill_value=0)
source_counts["Percentage Real (%)"]=(source_counts['Real']/(source_counts['Real']+source_counts['Fake']))*100
source_counts["Percentage Fake (%)"]=(source_counts['Fake']/(source_counts['Real']+source_counts['Fake']))*100

sorted_sources=source_counts.sort_values(by='Percentage Real (%)',ascending=False)
print("Top 10 Most Credible News Sources:")
for source, row in sorted_sources.head(10).iterrows():
    print(f"News {source},fake news= {row['Percentage Fake (%)']:.1f}%")
    
print("Top 10 Least Credible News Sources:")
for source, row in sorted_sources.tail(10).iterrows():
    print(f"News {source},fake news= {row['Percentage Fake (%)']:.1f}%")
    
######################### detecting keywords associated with fake news #########################
stop_words = set(stopwords.words("english"))

title_counter = Counter()
text_counter = Counter()

for index, row in cleaned_dataset.iterrows():
  title_words = word_tokenize(row["title"])
  text_words = word_tokenize(row["text"])

  title_words = [word.lower() for word in title_words if word.isalpha() and word.lower() not in stop_words]
  text_words = [word.lower() for word in text_words if word.isalpha() and word.lower() not in stop_words]

  if row["label"] == "Fake":
    title_counter.update(title_words)
    text_counter.update(text_words)

top_keywords_title = title_counter.most_common(5)
top_keywords_text = text_counter.most_common(5)

print("Top 5 Keywords Associated with Fake News Titles:")
for keyword, count in top_keywords_title:
  print(f"{keyword}:{count} times")
print("Top 5 Keywords Associated with Fake News Texts:")
for keyword, count in top_keywords_text:
  print(f"{keyword}:{count} times")

######################### titles and text correlation analysis #########################
cleaned_dataset['title_length']=cleaned_dataset['title'].apply(len)
cleaned_dataset['text_length']=cleaned_dataset['text'].apply(len)

real_news=cleaned_dataset[cleaned_dataset['label']=='Real']
fake_news=cleaned_dataset[cleaned_dataset['label']=='Fake']

avg_real_title_length=real_news['title_length'].mean()
avg_fake_title_length=fake_news['title_length'].mean()
avg_real_text_length=real_news['text_length'].mean()
avg_fake_text_length=fake_news['text_length'].mean()

print(f'Average Title Length for Real News: {avg_real_title_length:.2f} characters')
print(f'Average Title Length for Fake News: {avg_fake_title_length:.2f} characters')
print(f'Average Text Length for Real News: {avg_real_text_length:.2f} characters')
print(f'Average Text Length for Fake News: {avg_fake_text_length:.2f} characters')
# we see that fake news are about to have more words in the title and less words in the text

#we visualize data
labels=['Real Title','Fake Title','Real Text','Fake Text']
length=[avg_real_title_length,avg_fake_title_length,avg_real_text_length,avg_fake_text_length]

plt.figure(figsize=(10,6))
colors=['green','red','green','red']
plt.bar(labels,length,color=colors)
plt.title('Average Title and Text Lengths for Real and Fake News')
plt.ytitle('Average Length')
plt.xticks(rotation=45)
plt.show()

######################### detecting sensationalism in Fake News - sensational words #########################
def detect_sensationalism(text):
  sensetional_keywords=['shocking','outrageous','unbelievable','mind-blowing','explosive']
  for keyword in sensetional_keywords:
    if re.search(r'\b'+keyword+ r'\b',text, re.IGNORECASE):
      return True
    return False
  
cleaned_dataset['Sensationalism']=cleaned_dataset['text'].apply(detect_sensationalism)
contigency_table=pd.crosstab(cleaned_dataset['Sensationalism'],cleaned_dataset['label'])
print(contigency_table)
#1252 fake news that do not have any sensational keyword
#746 real news that do not have any sensational keyword
#29 fake news that have sensational keyword
#8 real news that have sensational keyword

chi2,p,_,_=chi2_contingency(contigency_table)
print(f'Chi-squared statistics: {chi2}')
print(f'P-value: {p}')

#test with significance level a=0.05.If p-value<a theres a significant association between sensationalism and credibility of news
#and the opposite
alpha=0.05
if p < alpha:
  print('There is a significant association between sensationalism and credibility of news')
else:
  print('There is not a significant association between sensationalism and credibility of news')


######################### analyzing Emotion in Fake News using NLP #########################
nltk.download('vader_lexicon')
analyzer=SentimentIntensityAnalyzer()

def analyze_sentiments(text):
  sentiment_scores=analyzer.polarity_scores(text)
  #check if sentiment score is greater than 0.05 then its returning positive that means emotion detection is positive
  if sentiment_scores['compound']>=0.05:
    return 'Positive'
  elif sentiment_scores['compound']<.05:
    return 'Negative'
  else:
    return 'Neutral'
cleaned_dataset['Sentiment']=cleaned_dataset['text'].apply(analyze_sentiments)
print(cleaned_dataset[['text','Sentiment']].head())

######################### detect fake news with future engineering #########################

#feature 1
fake_news_data=cleaned_dataset[cleaned_dataset['label']=='Fake']
vectorizer=CountVectorizer(stop_words='english')
X=vectorizer.fit_transform(fake_news_data['text'])
#word_frequenceis represents words that are associated with fake news
word_frequencies=X.toarray().sum(axis=0)
feature_names=vectorizer.get_feature_names_out()
keywords=[feature_names[i] for i in word_frequencies.argsort()[-10:][::-1]]
print(keywords)

#now we will calculate the percentage of its users in site URL column using fake news percentage
#feature 2
site_counts=cleaned_dataset['site_url'].value_counts()
print(site_counts)
fake_site_counts=cleaned_dataset[cleaned_dataset['label']=='Fake']['site_url'].value_counts()
fake_new_percentage=fake_site_counts/site_counts

#now we create a function to predict if the news are fake or real based on these 2 features
def fake_news_predictions(title,news_source):
  #first step ths function will check if title contains any of the keywords associated with fake news
  title_contains_keywords=any(keyword in title.lower() for keyword in keywords)
  if news_source in fake_new_percentage:
    source_fake_percentage=fake_new_percentage[news_source]
  else:
    source_fake_percentage=0.0

 #we define a simple rule for making the predictions
  if title_contains_keywords and source_fake_percentage >0.5: #this threshold its up to us
    return "Fake News"
#the higher the percentage fake news reported,it means the number is closer to one.And the exact opposite
#closer to zero the higher the probability that the news are real because the percentage of fake news reported is going to be very low
  else:
    return "Real News"

#example 1
text_input1='Breaking a new planet has been discovered by scientists'
source_input1='100percentfedup.com'
prediction1=fake_news_predictions(text_input1,source_input1)
print(f'Prediction: {prediction1}')

#example 2
text_input2='Hillary Clinton and Donald Trump said that going to be married'
source_input2='der-postillon.com'
prediction2=fake_news_predictions(text_input2,source_input2)
print(f'Prediction: {prediction2}')

######################### Detecting Fake News with Logistic Regression #########################
missing_data=cleaned_dataset[['text','label']].isnull().any(axis=1)
if missing_data.any():
  print('Missing Values Found In The Dataset. Handle Missing Values Before Proceeding')
else:
  le=LabelEncoder()
  cleaned_dataset['label']=le.fit_transform(cleaned_dataset['label'])
  X=cleaned_dataset['text']
  y=cleaned_dataset['label']
  X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)
  #next we create a pipeline for text feature extraction and logistic regression
  text_feature_extractions=TfidfVectorizer(max_features=5000,stop_words='english')
  #initialize the model
  model=LogisticRegression()
  #initialize the pipline
  pipeline=Pipeline([
    ('tfidf',text_feature_extractions),
    ('model',model)
  ])
  pipeline.fit(X_train,y_train)
  #make predictions
  y_pred=pipeline.predict(X_test)
  #find accuracy
  accuracy=accuracy_score(y_test,y_pred)
  #print results
  print(f'Accuracy: {accuracy:.2f}')
  
  #define function to predict fake news
  def fakenewspredictions(text):
    input_data=[text]
    prediction=pipeline.predict(input_data)
    if prediction[0]==0:
      return 'Real News'
    else:
      return 'Fake News'
  
#lets test this model
article_input="""
Olympiacos has had a rough time with its transfers this year. Willian, Velde, Yaremchuk, who came to make a difference, are not making it. Mouzakitis and
Kostoulas are making it .
Unlike the new ones, the old ones are still remembered. Carmo, who came from Porto on loan from Nottingham Forest, is still being sought.
But he will find it.Horta is in Braga, although he no longer plays. Olympiacos, however, still lacks a reliable winger.And the one who left where he went
is not playing.
Daniel Podence has not played a single minute in Al Shabab. An injury in early September took him back. But the reports said he would be out for 3 weeks.
Podence still hasn't played.Therefore, it is logical and next. The rumors are intense, even if the discussions in the summer left some disagreements.
These are being overcome. Saudi Arabia has not kept others and others. Some consider it very likely. Pontense will sooner or later return to Greece.
"""
prediction=fakenewspredictions(article_input)
print(f'Prediction: {prediction}')
  
  
  
  
  
  
  
  