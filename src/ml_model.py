import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load the collected data
data = pd.read_csv('resource_usage_data.csv')

# Split the data into features and labels
X = data[['cpu_usage', 'io_usage', 'user_interactions']]
y = data['video_playing']  # Label indicating whether a video is playing

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Model accuracy: {accuracy:.2f}')

# Save the trained model
joblib.dump(model, 'video_activity_model.pkl')
