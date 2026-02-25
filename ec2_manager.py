import boto3
import logging
import os
import sys
from dotenv import load_dotenv

# 🔥 Load .env
load_dotenv()

# ---------- CONFIG ----------
REGION = os.getenv("AWS_REGION", "ap-south-1")
AMI_ID = os.getenv("AMI_ID")
INSTANCE_TYPE = os.getenv("INSTANCE_TYPE", "t2.micro")
KEY_NAME = os.getenv("KEY_NAME")
SECURITY_GROUP_ID = os.getenv("SECURITY_GROUP_ID")
SUBNET_ID = os.getenv("SUBNET_ID")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "DevOps-Auto-Instance")

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

# ---------- AWS ----------
ec2 = boto3.resource("ec2", region_name=REGION)
ec2_client = boto3.client("ec2", region_name=REGION)


# =========================================================
# 🔥 Get managed instances
# =========================================================
def get_managed_instances():
    filters = [
        {"Name": "tag:Name", "Values": [f"{INSTANCE_NAME} *"]},
        {
            "Name": "instance-state-name",
            "Values": ["pending", "running", "stopping", "stopped"],
        },
    ]

    response = ec2_client.describe_instances(Filters=filters)

    instances = []
    for res in response["Reservations"]:
        for inst in res["Instances"]:
            name = ""
            for tag in inst.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            instances.append(
                {
                    "InstanceId": inst["InstanceId"],
                    "Name": name,
                    "State": inst["State"]["Name"],
                }
            )
    return instances


# =========================================================
# 🔥 Generate next instance name
# =========================================================
def generate_next_name():
    instances = get_managed_instances()

    numbers = []
    for inst in instances:
        try:
            num = int(inst["Name"].split()[-1])
            numbers.append(num)
        except Exception:
            pass

    next_num = max(numbers, default=0) + 1
    return f"{INSTANCE_NAME} {next_num:02d}"


# =========================================================
# 🚀 Create instances
# =========================================================
def create_instances():
    try:
        count = int(input("How many instances to create? ").strip())
        if count <= 0:
            print("❌ Invalid number")
            return

        print(f"🚀 Creating {count} instance(s)...")

        instances = ec2.create_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            SecurityGroupIds=[SECURITY_GROUP_ID],
            SubnetId=SUBNET_ID,
            MinCount=count,
            MaxCount=count,
        )

        created_ids = []

        for instance in instances:
            name = generate_next_name()

            ec2_client.create_tags(
                Resources=[instance.id],
                Tags=[{"Key": "Name", "Value": name}],
            )

            created_ids.append(instance.id)
            print(f"✅ Created: {instance.id} ({name})")

        print("⏳ Waiting for instances to run...")
        ec2_client.get_waiter("instance_running").wait(
            InstanceIds=created_ids
        )

        print("✅ All instances running")

    except Exception as e:
        logging.error(f"Creation failed: {e}")
        print(f"❌ Creation failed: {e}")


# =========================================================
# 📋 List instances
# =========================================================
def list_instances():
    instances = get_managed_instances()

    if not instances:
        print("❌ No managed instances found")
        return []

    print("\n📋 Managed Instances:")
    for idx, inst in enumerate(instances, start=1):
        print(
            f"{idx}. {inst['Name']} | {inst['InstanceId']} | {inst['State']}"
        )

    return instances


# =========================================================
# ▶️ Start specific instance
# =========================================================
def start_instance():
    instances = list_instances()
    if not instances:
        return

    choice = int(input("Select instance number to START: "))
    inst = instances[choice - 1]

    if inst["State"] != "stopped":
        print("❌ Instance must be in stopped state")
        return

    ec2_client.start_instances(InstanceIds=[inst["InstanceId"]])
    print(f"✅ Starting {inst['Name']}")


# =========================================================
# ⏹️ Stop specific instance
# =========================================================
def stop_instance():
    instances = list_instances()
    if not instances:
        return

    choice = int(input("Select instance number to STOP: "))
    inst = instances[choice - 1]

    if inst["State"] != "running":
        print("❌ Instance must be running")
        return

    ec2_client.stop_instances(InstanceIds=[inst["InstanceId"]])
    print(f"✅ Stopping {inst['Name']}")


# =========================================================
# 🗑️ Terminate specific instance
# =========================================================
def terminate_instance():
    instances = list_instances()
    if not instances:
        return

    choice = int(input("Select instance number to TERMINATE: "))
    inst = instances[choice - 1]

    confirm = input(
        f"⚠️ Confirm terminate {inst['Name']}? (yes/no): "
    ).lower()

    if confirm != "yes":
        print("Cancelled.")
        return

    ec2_client.terminate_instances(InstanceIds=[inst["InstanceId"]])
    print(f"✅ Terminated {inst['Name']}")


# =========================================================
# ▶️ Start ALL instances
# =========================================================
def start_all_instances():
    instances = get_managed_instances()

    to_start = [
        inst["InstanceId"]
        for inst in instances
        if inst["State"] == "stopped"
    ]

    if not to_start:
        print("❌ No stopped instances to start")
        return

    ec2_client.start_instances(InstanceIds=to_start)
    print(f"✅ Starting instances: {to_start}")


# =========================================================
# ⏹️ Stop ALL instances
# =========================================================
def stop_all_instances():
    instances = get_managed_instances()

    to_stop = [
        inst["InstanceId"]
        for inst in instances
        if inst["State"] == "running"
    ]

    if not to_stop:
        print("❌ No running instances to stop")
        return

    ec2_client.stop_instances(InstanceIds=to_stop)
    print(f"✅ Stopping instances: {to_stop}")


# =========================================================
# 🗑️ Terminate ALL instances
# =========================================================
def terminate_all_instances():
    instances = get_managed_instances()

    if not instances:
        print("❌ No instances found")
        return

    ids = [inst["InstanceId"] for inst in instances]

    confirm = input(
        f"⚠️ TERMINATE ALL {len(ids)} instances? (yes/no): "
    ).lower()

    if confirm != "yes":
        print("Cancelled.")
        return

    ec2_client.terminate_instances(InstanceIds=ids)
    print(f"✅ Terminated instances: {ids}")


# =========================================================
# 🧠 Main Menu
# =========================================================
def main():
    print("\n====== EC2 MANAGER ======")
    print("1. Create Instance(s)")
    print("2. Start Instance")
    print("3. Stop Instance")
    print("4. Terminate Instance")
    print("5. Start ALL Instances")
    print("6. Stop ALL Instances")
    print("7. Terminate ALL Instances")
    print("=========================")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        create_instances()
    elif choice == "2":
        start_instance()
    elif choice == "3":
        stop_instance()
    elif choice == "4":
        terminate_instance()
    elif choice == "5":
        start_all_instances()
    elif choice == "6":
        stop_all_instances()
    elif choice == "7":
        terminate_all_instances()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)