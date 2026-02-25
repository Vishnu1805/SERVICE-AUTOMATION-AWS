# 🚀 AWS EC2 Automation with Python (boto3)

Automates AWS EC2 lifecycle operations using Python and boto3 

---

## ✨ Features

* ✅ Create EC2 instances
* ▶️ Start EC2 instances
* ⏹️ Stop EC2 instances
* ❌ Terminate EC2 instances
* 🏷️ Auto-generated unique instance names
* 📄 Logging to file (`ec2_manager.log`)
* 🔐 Environment-based configuration

---

## 🧠 Project Structure

```
SERVICE-AUTOMATION-AWS/
│
├── .venv/                 # Python virtual environment (ignored)
├── .env                   # Environment variables (DO NOT COMMIT)
├── .gitignore             # Git ignore rules
├── ec2_manager.py         # Main automation script
├── ec2_manager.log        # Runtime logs
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## 🛠️ Tech Stack

* Python 3
* boto3
* python-dotenv
* AWS EC2

---

## 📦 Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Vishnu1805/SERVICE-AUTOMATION-AWS.git

cd SERVICE-AUTOMATION-AWS


### 2️⃣ Create virtual environment (recommended)

```bash
python -m venv .venv
```


### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure environment variables

Create a `.env` file in the root:

```env
AWS_REGION=ap-south-1
AMI_ID=ami-xxxxxxxx
INSTANCE_TYPE=t2.micro
KEY_NAME=your-key
SECURITY_GROUP_ID=sg-xxxxxxxx
SUBNET_ID=subnet-xxxxxxxx
INSTANCE_NAME=DevOps-Auto-Instance
```

## ▶️ Run the Application

```bash
python ec2_manager.py
```

You will see:

```
====== EC2 MANAGER ======
1. Create Instance(s)
2. Start Instance
3. Stop Instance
4. Terminate Instance
5. Start ALL Instances
6. Stop ALL Instances
7. Terminate ALL Instances
=========================

```

---

## 📄 Logging

Application logs are written to:

```
ec2_manager.log
```

This helps in production debugging and auditing.

---

## 🔐 AWS Permissions Required

Your IAM user/role must have permissions for:

* ec2:RunInstances
* ec2:StartInstances
* ec2:StopInstances
* ec2:TerminateInstances
* ec2:DescribeInstances

---
