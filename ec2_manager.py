import boto3
import logging
import os
import sys
from dotenv import load_dotenv

# 🔥 Load .env
load_dotenv()

# ---------- CONFIG FROM ENV ----------
REGION = os.getenv("AWS_REGION", "ap-south-1")
AMI_ID = os.getenv("AMI_ID")
INSTANCE_TYPE = os.getenv("INSTANCE_TYPE", "t2.micro")
KEY_NAME = os.getenv("KEY_NAME")
SECURITY_GROUP_ID = os.getenv("SECURITY_GROUP_ID")
SUBNET_ID = os.getenv("SUBNET_ID")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "DevOps-Auto-Instance")
# ------------------------------------

# ---------- VALIDATION ----------
REQUIRED_VARS = {
    "AMI_ID": AMI_ID,
    "KEY_NAME": KEY_NAME,
    "SECURITY_GROUP_ID": SECURITY_GROUP_ID,
    "SUBNET_ID": SUBNET_ID,
}

missing = [k for k, v in REQUIRED_VARS.items() if not v]

if missing:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing)}"
    )

# ---------- LOGGING ----------
logging.basicConfig(
    filename="ec2_manager.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info(f"Starting EC2 Manager in region: {REGION}")

# ---------- AWS CLIENTS ----------
ec2 = boto3.resource("ec2", region_name=REGION)
ec2_client = boto3.client("ec2", region_name=REGION)


# 🔥 Generate unique instance name
def generate_instance_name():
    try:
        filters = [{"Name": "tag:Name", "Values": [f"{INSTANCE_NAME}-*"]}]
        response = ec2_client.describe_instances(Filters=filters)

        count = 0
        for res in response["Reservations"]:
            count += len(res["Instances"])

        new_name = f"{INSTANCE_NAME}-{count + 1:03d}"
        return new_name

    except Exception as e:
        logging.error(f"Name generation failed: {e}")
        return f"{INSTANCE_NAME}-manual"


# 🚀 Create Instance
def create_instance():
    try:
        print("🚀 Creating EC2 instance...")

        # 🔥 unique name
        instance_name_unique = generate_instance_name()
        print(f"📝 Assigning name: {instance_name_unique}")

        instances = ec2.create_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            SecurityGroupIds=[SECURITY_GROUP_ID],
            SubnetId=SUBNET_ID,
            MinCount=1,
            MaxCount=2,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": instance_name_unique}],
                }
            ],
        )

        instance_id = instances[0].id
        logging.info(f"Instance created: {instance_id}")
        print(f"✅ Instance created: {instance_id} ({instance_name_unique})")

        print("⏳ Waiting for instance to reach running state...")
        ec2_client.get_waiter("instance_running").wait(
            InstanceIds=[instance_id]
        )
        print("✅ Instance is now running")

        return instance_id

    except Exception as e:
        logging.error(f"Creation failed: {e}")
        print(f"❌ Instance creation failed: {e}")
        return None


# 🔍 Get ALL instances by base name
def get_instances_by_name(name):
    try:
        filters = [
            {"Name": "tag:Name", "Values": [f"{name}-*"]},
            {
                "Name": "instance-state-name",
                "Values": ["pending", "running", "stopping", "stopped"],
            },
        ]

        response = ec2_client.describe_instances(Filters=filters)

        instance_ids = []

        for res in response["Reservations"]:
            for inst in res["Instances"]:
                instance_ids.append(inst["InstanceId"])

        return instance_ids

    except Exception as e:
        logging.error(f"Lookup failed: {e}")
        print(f"❌ Lookup failed: {e}")
        return []


# ▶️ Start Instances (bulk)
def start_instances(instance_ids):
    if not instance_ids:
        print("❌ No instances found.")
        return

    try:
        ec2_client.start_instances(InstanceIds=instance_ids)
        logging.info(f"Started instances: {instance_ids}")
        print(f"✅ Started instances: {instance_ids}")
    except Exception as e:
        logging.error(f"Start failed: {e}")
        print(f"❌ Start failed: {e}")


# ⏹️ Stop Instances (bulk)
def stop_instances(instance_ids):
    if not instance_ids:
        print("❌ No instances found.")
        return

    try:
        ec2_client.stop_instances(InstanceIds=instance_ids)
        logging.info(f"Stopped instances: {instance_ids}")
        print(f"✅ Stopped instances: {instance_ids}")
    except Exception as e:
        logging.error(f"Stop failed: {e}")
        print(f"❌ Stop failed: {e}")


# 🗑️ Terminate Instances (bulk)
def terminate_instances(instance_ids):
    if not instance_ids:
        print("❌ No instances found.")
        return

    try:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        logging.info(f"Terminated instances: {instance_ids}")
        print(f"✅ Terminated instances: {instance_ids}")
    except Exception as e:
        logging.error(f"Terminate failed: {e}")
        print(f"❌ Terminate failed: {e}")


# 🧠 Main Menu
def main():
    print("\n====== EC2 MANAGER ======")
    print("1. Create Instance")
    print("2. Start Instance")
    print("3. Stop Instance")
    print("4. Terminate Instance")
    print("=========================")

    choice = input("Enter choice: ").strip()

    # 🚀 Create
    if choice == "1":
        create_instance()

    # 🔄 Bulk operations
    elif choice in ["2", "3", "4"]:
        instance_ids = get_instances_by_name(INSTANCE_NAME)

        if not instance_ids:
            print("❌ Instance not found. Create it first.")
            return

        if choice == "2":
            start_instances(instance_ids)

        elif choice == "3":
            stop_instances(instance_ids)

        elif choice == "4":
            confirm = input("⚠️ Are you sure to TERMINATE? (yes/no): ").lower()
            if confirm == "yes":
                terminate_instances(instance_ids)
            else:
                print("Termination cancelled.")

    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
