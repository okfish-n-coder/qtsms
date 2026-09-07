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


def main():
    parser = argparse.ArgumentParser(
        description="Send SMS via Beeline A2P Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --api-key my_api_key --phone +79991234567 --text "Hello World"
  %(prog)s --token my_token --phone +79991234567 --text "Hello World" --sender MyCompany
  %(prog)s --api-key my_api_key --phone +79991234567 --text "Test" --use-json
        """
    )
    
    # Authentication options (mutually exclusive group)
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument(
        "--api-key",
        type=str,
        help="API key for basic authentication"
    )
    auth_group.add_argument(
        "--token",
        type=str,
        help="Token for X-ApiKey header authentication"
    )
    
    # Required arguments
    parser.add_argument(
        "--phone",
        type=str,
        required=True,
        help="Recipient phone number in international format (e.g., +79991234567)"
    )
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="SMS message text"
    )
    
    # Optional arguments
    parser.add_argument(
        "--sender",
        type=str,
        default=None,
        help="Sender name (alphanumeric sender ID)"
    )
    parser.add_argument(
        "--use-json",
        action="store_true",
        help="Use JSON format for request (default: XML)"
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default=None,
        help="Optional batch ID for grouping messages"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize client based on authentication method
        if args.api_key:
            if args.verbose:
                print(f"Initializing client with API key: {args.api_key[:4]}...")
            client = QTSMSClient(api_key=args.api_key, use_json=args.use_json)
        else:
            if args.verbose:
                print(f"Initializing client with token auth")
            client = QTSMSClient.with_token_auth(api_key=args.token, use_json=args.use_json)
        
        if args.verbose:
            print(f"Sending SMS to {args.phone}")
            print(f"Message: {args.text}")
            if args.sender:
                print(f"Sender: {args.sender}")
            print(f"Using JSON format: {args.use_json}")
        
        # Send SMS
        response = client.send_sms(
            phone=args.phone,
            text=args.text,
            sender=args.sender,
            batch_id=args.batch_id
        )
        
        if args.verbose:
            print("\n=== Response ===")
            print(f"Raw response: {response}")
        
        # Parse and display result
        if hasattr(response, 'actions'):
            # Pydantic model response (JSON mode)
            for action in response.actions:
                print(f"✓ Message sent successfully!")
                print(f"  Phone: {action.phone}")
                print(f"  Status: {action.status}")
                print(f"  Batch ID: {action.batch_id}")
                if hasattr(action, 'id') and action.id:
                    print(f"  Message ID: {action.id}")
        else:
            # XML response or simple success
            print(f"✓ SMS sent successfully to {args.phone}")
            if isinstance(response, dict):
                for key, value in response.items():
                    print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error: {error_msg}", file=sys.stderr)
        
        # Try to provide helpful error messages
        error_code = None
        for code, _ in QTMSErrorCode.get_all_errors().items():
            if code.lower() in error_msg.lower():
                error_code = code
                break
        
        if error_code:
            description = QTMSErrorCode.get_error_message(error_code)
            print(f"  Error code: {error_code}", file=sys.stderr)
            print(f"  Description: {description}", file=sys.stderr)
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
