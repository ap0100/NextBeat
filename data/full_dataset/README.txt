The dataset contains 444 physiological recordings and 148 reference values (simultaneous acquisition of dual-wavelength PPG signals with 1-leadECG signals,cuffed blood pressure values) from 148 subjects in three different exercise states.
The dataset is designed to support cuffless blood pressure estimation, PPG signal analysis, PPG signal reconstruction of ECG signals, and wearable health technology robustness in wearable devices,development of cardiovascular monitoring technologies.

All data were collected with informed consent and institutional medical ethics approval was obtained." information.csv", records basic information for all subjects, including unique identification IDs age, gender, height, weight, SBP, DBP, and HR.

The The dataset consists of two folders. The Raw_Data folder contains the original data files collected in csv format. Each file includes four signal segments. 
The first column, labeled ECG_I, stores the original ECG signal. The second column, labeled PPG_RED, stores the original PPG signal measured in red light. 
The second column, labeled PPG_RED, stores the original PPG signal measured in red light. 
The third column, labeled PPG_IR, stores the original PPG signal measured in infrared light. 
Fourth column is a string labeled {'Hz': 250}; it does not contain signal data and only records the sampling rate. Note that files in the Raw_Data folder span more than 180 s of recording and exceed 45,000 samples.

The files in the Filtered_Data folder are csvs exported by the self-developed host computer software. Each file contains five signal segments. Column 1, ECG_I_Filtered, stores the filtered ECG signal. Column 2, ECG_I_mv, stores the ECG signal converted to millivolts and is of floating-point type. Column 3, PPG_RED_Filtered, stores the filtered red PPG signal and is floating-point. 
Column 4, PPG_IR_Filtered, stores the filtered infrared PPG signal and is floating-point. Column 5 stores the sampling rate and the ECG voltage conversion formula.Note that some subjects in the Filtered_Data folder have less than 180 s of filtered data (fewer than 45,000 samples) because of the equipment used during measurement.

In both the Raw_Data and Filtered_Data folders, file names follow the format 000_x, where "000" denotes the subject ID and "x" denotes the subject's state during acquisition; "x" takes the values 1, 2, or 3, which correspond to three different states. 
Thus, each ID has three csv waveform files, for example 001_1.csv, 001_2.csv, and 001_3.csv, representing synchronized PPG and ECG signals recorded under three different conditions. 
Note that blood pressure was measured only in the resting state and not after exercise; therefore, blood pressure values appear only in the csv file ending with "_1" for each ID.


The above dataset is collected and managed by CardioWorks Team. If you have any questions about the data or relative researches, please contact us by email: lishiyong@guet.edu.cn.