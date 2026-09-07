#!/usr/bin/env python3
"""
Example CLI utility to send SMS via Beeline A2P Gateway.

Usage:
    python send_sms.py --api-key YOUR_API_KEY --phone +79991234567 --text "Hello from Beeline!"
    python send_sms.py --token YOUR_TOKEN --phone +79991234567 --text "Hello from Beeline!"
    python send_sms.py --help
"""

import argparse
import sys
from qtsms_client import QTSMSClient, QTMSErrorCode


def create_client(api_key: str = None, token: str = None, use_json: bool = False) -> QTSMSClient:
    """Create QTSMSClient with appropriate authentication method."""
    if token:
        return QTSMSClient.with_token_auth(api_key=token)
    return QTSMSClient(api_key=api_key, use_json=use_json)


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
  %(prog)s --api-key my_api_key --phone +79991234567 --text "Hello World"
  %(prog)s --token my_token --phone +79991234567 --text "Hello World" --sender MyCompany
        """
    )
    
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument("--api-key", type=str, help="API key for authentication")
    auth_group.add_argument("--token", type=str, help="Token for X-ApiKey header authentication")
    
    parser.add_argument("--phone", type=str, required=True, help="Recipient phone (e.g., +79991234567)")
    parser.add_argument("--text", type=str, required=True, help="SMS message text")
    parser.add_argument("--sender", type=str, default=None, help="Sender name (alphanumeric ID)")
    parser.add_argument("--batch-id", type=str, default=None, help="Optional batch ID")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    try:
        client = create_client(api_key=args.api_key, token=args.token)
        
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
