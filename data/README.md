# 📊 Data Used for Training 

The `train_and_test_data` folder contains the training and testing data used for the model, derived from the public Mendeley ECG+PPG Dataset.

- **🩺 Filtered subset:** Only 30 patients from the full dataset are used to keep training resource requirements manageable.
- **👤 Demographics:** The relevant `information.csv` data is included to reduce demographic bias. The model is trained using demographic features, but these are not currently available for testing on the physical prototype.
- **🧪 Data split:** Contains the prepared training and testing samples used by the model.
