#!/usr/bin/env python3
"""
Example CLI utility to send SMS via Beeline A2P Gateway.

Usage:
    # With username/password authentication
    python send_sms.py --user my_login --password my_pass --phone +79991234567 --text "Hello!"
    
    # With token authentication (X-ApiKey header)
    python send_sms.py --token YOUR_TOKEN --phone +79991234567 --text "Hello!"
    
    python send_sms.py --help
"""

import argparse
import sys
from qtsms_client import QTSMSClient, QTMSErrorCode


def create_client(user: str = None, password: str = None, token: str = None) -> QTSMSClient:
    """Create QTSMSClient with appropriate authentication method."""
    if token:
        return QTSMSClient.with_token_auth(api_key=token)
    return QTSMSClient(user=user, password=password)


def print_success(response, verbose: bool = False):
    """Print successful SMS send result."""
    if hasattr(response, 'actions'):
        for action in response.actions:
            print(f"✓ Message sent successfully!")
            print(f"  Phone: {action.phone}")
            print(f"  Status: {action.status}")
            if action.batch_id:
                print(f"  Batch ID: {action.batch_id}")
            if hasattr(action, 'id') and action.id:
                print(f"  Message ID: {action.id}")
    else:
        print(f"✓ SMS sent successfully")
        if isinstance(response, dict):
            for key, value in response.items():
                print(f"  {key}: {value}")


def print_error(error: Exception, error_code_class, verbose: bool = False):
    """Print error with description if available."""
    error_msg = str(error)
    print(f"✗ Error: {error_msg}", file=sys.stderr)
    
    # Try to find error code in message
    for code, _ in error_code_class.get_all_errors().items():
        if code.lower() in error_msg.lower():
            description = error_code_class.get_error_message(code)
            print(f"  Error code: {code}", file=sys.stderr)
            print(f"  Description: {description}", file=sys.stderr)
            break
    
    if verbose:
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="Send SMS via Beeline A2P Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user my_login --password my_pass --phone +79991234567 --text "Hello World"
  %(prog)s --token my_token --phone +79991234567 --text "Hello World" --sender MyCompany
        """
    )
    
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument("--user", type=str, help="Username for authentication")
    auth_group.add_argument("--token", type=str, help="Token for X-ApiKey header authentication")
    
    parser.add_argument("--password", type=str, required=False, help="Password for authentication (required with --user)")
    parser.add_argument("--phone", type=str, required=True, help="Recipient phone (e.g., +79991234567)")
    parser.add_argument("--text", type=str, required=True, help="SMS message text")
    parser.add_argument("--sender", type=str, default=None, help="Sender name (alphanumeric ID)")
    parser.add_argument("--batch-id", type=str, default=None, help="Optional batch ID")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Validate that password is provided when using user auth
    if args.user and not args.password:
        print("Error: --password is required when using --user", file=sys.stderr)
        return 1
    
    try:
        client = create_client(user=args.user, password=args.password, token=args.token)
        
        if args.verbose:
            print(f"Sending SMS to {args.phone}")
            print(f"Message: {args.text}")
            if args.sender:
                print(f"Sender: {args.sender}")
        
        response = client.send_sms(
            phone=args.phone,
            text=args.text,
            sender=args.sender,
            batch_id=args.batch_id
        )
        
        print_success(response, args.verbose)
        return 0
        
    except Exception as e:
        print_error(e, QTMSErrorCode, args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
