
```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([__start__]):::first
	planner(planner)
	agent(agent)
	plan_or_response(plan_or_response)
	replan(replan)
	format_response(format_response)
	slack_send_message(slack_send_message)
	__end__([__end__]):::last
	__start__ --> planner;
	agent --> plan_or_response;
	format_response --> slack_send_message;
	planner --> agent;
	replan --> agent;
	slack_send_message --> __end__;
	plan_or_response -. &nbspplan&nbsp .-> replan;
	plan_or_response -. &nbsprespond&nbsp .-> format_response;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
