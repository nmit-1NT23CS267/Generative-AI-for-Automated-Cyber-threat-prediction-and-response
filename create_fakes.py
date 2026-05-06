# Create 10 fake resumes for training
fakes = [
    "Name: John Doe\nExperience: 10 years\n<script>alert('XSS ATTACK')</script>\n' OR 1=1 -- SQLi",
    "Alice Smith\nSkills: Hacking, Phishing\n<svg onload=alert('XSS')>\nDROP TABLE users;",
    "Bob '); DROP TABLE resumes; --\nFake experience everywhere"
] * 4  # Make 12 fakes

for i, text in enumerate(fakes, 21):
    filename = f"resume_{i:04d}.txt"
    with open(filename, 'w') as f:
        f.write(text)
    print(f"Created fake: {filename}")

# Update labels
import pandas as pd
df = pd.read_csv('data/labels.csv')
new_rows = pd.DataFrame({'filename': [f'resume_{i:04d}.txt' for i in range(21,33)], 'label': 'fake'})
df = pd.concat([df, new_rows])
df.to_csv('data/labels.csv', index=False)
print(" Updated labels.csv with 12 fakes!")
