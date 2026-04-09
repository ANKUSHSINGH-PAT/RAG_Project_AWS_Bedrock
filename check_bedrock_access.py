import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print("[OK] AWS Credentials are configured")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        return True
    except NoCredentialsError:
        print("[ERROR] No AWS credentials found")
        print("   Please configure AWS credentials using:")
        print("   - AWS CLI: aws configure")
        print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("   - AWS credentials file: ~/.aws/credentials")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking credentials: {str(e)}")
        return False

def check_bedrock_access():
    """Check Bedrock service access"""
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        print("\n[OK] Bedrock service is accessible in us-east-1")
        return True
    except ClientError as e:
        print(f"\n[ERROR] Cannot access Bedrock service: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error accessing Bedrock: {str(e)}")
        return False

def list_available_models():
    """List available foundation models in Bedrock"""
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        response = bedrock.list_foundation_models()
        
        print("\n[LIST] Available Foundation Models:")
        print("-" * 80)
        
        models_by_provider = {}
        for model in response['modelSummaries']:
            provider = model['providerName']
            if provider not in models_by_provider:
                models_by_provider[provider] = []
            models_by_provider[provider].append(model)
        
        for provider, models in sorted(models_by_provider.items()):
            print(f"\n{provider}:")
            for model in models:
                model_id = model['modelId']
                model_name = model['modelName']
                print(f"  - {model_name}")
                print(f"    ID: {model_id}")
                
        return True
    except ClientError as e:
        print(f"\n[ERROR] Cannot list models: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error listing models: {str(e)}")
        return False

def check_specific_models():
    """Check access to specific models used in the project"""
    models_to_check = [
        {
            'id': 'amazon.titan-embed-text-v1',
            'name': 'Amazon Titan Embeddings',
            'type': 'Embedding'
        },
        {
            'id': 'meta.llama3-8b-instruct-v1:0',
            'name': 'Meta Llama 3 8B Instruct',
            'type': 'LLM'
        }
    ]
    
    print("\n[CHECK] Checking Project-Specific Models:")
    print("-" * 80)
    
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    for model in models_to_check:
        try:
            # Try to invoke the model with a minimal request
            if model['type'] == 'Embedding':
                response = bedrock_runtime.invoke_model(
                    modelId=model['id'],
                    body=json.dumps({"inputText": "test"})
                )
                print(f"[OK] {model['name']} ({model['id']})")
                print(f"   Status: Accessible and working")
            elif model['type'] == 'LLM':
                response = bedrock_runtime.invoke_model(
                    modelId=model['id'],
                    body=json.dumps({
                        "prompt": "Hello",
                        "max_gen_len": 10,
                        "temperature": 0.1
                    })
                )
                print(f"[OK] {model['name']} ({model['id']})")
                print(f"   Status: Accessible and working")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"[ERROR] {model['name']} ({model['id']})")
            print(f"   Error: {error_code} - {error_msg}")
            
            if error_code == 'AccessDeniedException':
                print(f"   [WARNING] You need to request model access in AWS Bedrock console")
            elif error_code == 'ValidationException':
                print(f"   [WARNING] Model may not be available in your region")
        except Exception as e:
            print(f"[ERROR] {model['name']} ({model['id']})")
            print(f"   Error: {str(e)}")

def main():
    print("=" * 80)
    print("AWS BEDROCK ACCESS CHECK")
    print("=" * 80)
    
    # Check AWS credentials
    if not check_aws_credentials():
        return
    
    # Check Bedrock access
    if not check_bedrock_access():
        return
    
    # List all available models
    list_available_models()
    
    # Check specific models used in the project
    check_specific_models()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print("1. If you see 'AccessDeniedException' for any model:")
    print("   - Go to AWS Bedrock Console: https://console.aws.amazon.com/bedrock")
    print("   - Navigate to 'Model access' in the left sidebar")
    print("   - Request access for the required models")
    print("   - Wait for approval (usually instant for most models)")
    print("\n2. Ensure your IAM user/role has these permissions:")
    print("   - bedrock:InvokeModel")
    print("   - bedrock:InvokeModelWithResponseStream")
    print("   - bedrock:ListFoundationModels")
    print("\n3. Check that Bedrock is available in your region (us-east-1)")
    print("=" * 80)

if __name__ == "__main__":
    main()

# Made with Bob
