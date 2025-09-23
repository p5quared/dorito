import boto3
import time
from botocore.exceptions import ClientError

def remove_prefix_from_dynamodb(table_name, region='us-east-1', dry_run=True):
    """
    Remove RAW_DATA# prefix from dataId field in DynamoDB table
    
    Args:
        table_name (str): Name of the DynamoDB table
        region (str): AWS region
        dry_run (bool): If True, only print what would be changed without making updates
    """
    
    # Initialize DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=region)
    
    try:
        # Get table description to understand the key schema
        table_info = dynamodb.describe_table(TableName=table_name)
        key_schema = table_info['Table']['KeySchema']
        
        # Check if dataId is a key attribute
        is_key_attribute = any(key['AttributeName'] == 'dataId' for key in key_schema)
        
        print(f"Table: {table_name}")
        print(f"dataId is key attribute: {is_key_attribute}")
        print(f"Dry run mode: {dry_run}")
        print("-" * 50)
        
        # Scan the table
        scan_kwargs = {
            'TableName': table_name,
            'FilterExpression': 'begins_with(dataId, :prefix)',
            'ExpressionAttributeValues': {
                ':prefix': {'S': 'RAW_DATA#'}
            }
        }
        
        items_processed = 0
        items_updated = 0
        
        while True:
            response = dynamodb.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            for item in items:
                items_processed += 1
                current_data_id = item['dataId']['S']
                new_data_id = current_data_id.replace('RAW_DATA#', '', 1)
                
                print(f"Item {items_processed}:")
                print(f"  Current dataId: {current_data_id}")
                print(f"  New dataId: {new_data_id}")
                
                if not dry_run:
                    try:
                        if is_key_attribute:
                            # dataId is a key - need to create new item and delete old one
                            update_key_attribute(dynamodb, table_name, item, new_data_id)
                        else:
                            # dataId is regular attribute - can update in place
                            update_regular_attribute(dynamodb, table_name, item, new_data_id)
                        
                        items_updated += 1
                        print(f"  ✓ Updated successfully")
                        
                        # Add small delay to avoid throttling
                        time.sleep(0.1)
                        
                    except ClientError as e:
                        print(f"  ✗ Error updating item: {e}")
                else:
                    print(f"  [DRY RUN] Would update this item")
            
            # Check if there are more items to scan
            if 'LastEvaluatedKey' not in response:
                break
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        
        print("-" * 50)
        print(f"Total items processed: {items_processed}")
        if not dry_run:
            print(f"Total items updated: {items_updated}")
        else:
            print("This was a dry run. Set dry_run=False to perform actual updates.")
            
    except ClientError as e:
        print(f"Error accessing DynamoDB: {e}")

def update_regular_attribute(dynamodb, table_name, item, new_data_id):
    """Update dataId when it's a regular attribute"""
    # Get the key attributes for the update
    key = {}
    table_info = dynamodb.describe_table(TableName=table_name)
    
    for key_attr in table_info['Table']['KeySchema']:
        attr_name = key_attr['AttributeName']
        key[attr_name] = item[attr_name]
    
    # Update the item
    dynamodb.update_item(
        TableName=table_name,
        Key=key,
        UpdateExpression='SET dataId = :new_data_id',
        ExpressionAttributeValues={
            ':new_data_id': {'S': new_data_id}
        }
    )

def update_key_attribute(dynamodb, table_name, item, new_data_id):
    """Update dataId when it's a key attribute by creating new item and deleting old"""
    # Create new item with updated dataId
    new_item = item.copy()
    new_item['dataId']['S'] = new_data_id
    
    # Put new item
    dynamodb.put_item(
        TableName=table_name,
        Item=new_item
    )
    
    # Delete old item
    key = {}
    table_info = dynamodb.describe_table(TableName=table_name)
    
    for key_attr in table_info['Table']['KeySchema']:
        attr_name = key_attr['AttributeName']
        key[attr_name] = item[attr_name]
    
    dynamodb.delete_item(
        TableName=table_name,
        Key=key
    )

if __name__ == "__main__":
    # Configuration
    TABLE_NAME = "Reservoir"  # Replace with your actual table name
    REGION = "us-east-2"  # Replace with your AWS region
    
    # First run with dry_run=True to see what would be changed
    print("=== DRY RUN ===")
    remove_prefix_from_dynamodb(TABLE_NAME, REGION, dry_run=True)
    
    #Uncomment the following lines to perform actual updates
    print("\n=== ACTUAL UPDATE ===")
    user_input = input("Do you want to proceed with the actual update? (yes/no): ")
    if user_input.lower() == 'yes':
        remove_prefix_from_dynamodb(TABLE_NAME, REGION, dry_run=False)
