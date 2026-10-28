from analyzer import analyze_client_message

message = """
I need an e-commerce website with payment integration.
My budget is $300 and deadline is 10 days.
"""

result = analyze_client_message(message)

print(result)