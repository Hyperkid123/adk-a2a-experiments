from google.genai import types

async def callAgentAsync(query: str, runner, user_id, session_id):
  """Sends a query to the agent and prints the final response. Returns (final_response, tool_results)."""
  print(f"\n>>> User Query: {query}")

  # Prepare the user's message in ADK format
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response." # Default
  tool_results = []  # Capture tool call results

  # Key Concept: run_async executes the agent logic and yields Events.
  # We iterate through events to find the final answer.
  try:
      event_count = 0
      async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
          event_count += 1

          try:
              # Capture MCP tool results from FunctionResponse in event content
              if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                  for part in event.content.parts:
                      if hasattr(part, 'function_response') and part.function_response:
                          func_resp = part.function_response

                          # Extract the JSON result from the response content
                          if hasattr(func_resp, 'response') and func_resp.response:
                              response_content = func_resp.response.get('content', [])
                              if response_content and len(response_content) > 0:
                                  text_content = response_content[0].get('text', '')
                                  if text_content:
                                      try:
                                          import json
                                          result_data = json.loads(text_content)
                                          tool_results.append({
                                              'tool_name': func_resp.name,
                                              'result': result_data,
                                              'input': None  # Input not easily accessible in FunctionResponse
                                          })
                                      except json.JSONDecodeError as e:
                                          tool_results.append({
                                              'tool_name': func_resp.name,
                                              'result': text_content,
                                              'input': None
                                          })

              # Keep existing tool_calls capture for other action types (if any)
              if hasattr(event, 'actions') and event.actions:
                  if hasattr(event.actions, 'tool_calls'):
                      for tool_call in event.actions.tool_calls:
                          if hasattr(tool_call, 'result'):
                              tool_results.append({
                                  'tool_name': tool_call.name,
                                  'result': tool_call.result,
                                  'input': getattr(tool_call, 'input', None)
                              })

              # Key Concept: is_final_response() marks the concluding message for the turn.
              if event.is_final_response():
                  if event.content and event.content.parts:
                     # Assuming text response in the first part
                     final_response_text = event.content.parts[0].text
                  elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                     final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                  # Add more checks here if needed (e.g., specific error codes)
                  break # Stop processing events once the final response is found

          except Exception as e:
              print(f"  ⚠️ Error processing event #{event_count}: {e}")
              import traceback
              traceback.print_exc()


  except Exception as e:
      print(f"  ❌ Error in event loop: {e}")
      import traceback
      traceback.print_exc()
      final_response_text = f"Error during conversation: {e}"

  print(f"<<< Agent Response: {final_response_text}")
  return final_response_text, tool_results