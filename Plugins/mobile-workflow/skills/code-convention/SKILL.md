---
name: code-conventions
description: This document should allow us to follow the same code-writing style in our mobile apps. Use this when implementing code.
user-invocable: false
---

When writing code:
 - Set all the injections you need, the injected classes need to be declared as public properties;
 - Set all the public properties you need;
 - Set all the private properties you need, if a property will be used in the setter (if the property is encapsulated) of a public property you should use the "_" prefix;
 - Set the class constructor;
 - Set all the public methods you need, use the "Async" suffix for async tasks;
 - Set all the private methods you need, use the "Async" suffix for async tasks;

What we should avoid in our code:
 - We should avoid using "void" with async methods except for event handlers that require a void return type:
    private async void OnButtonClicked1(object? sender, EventArgs e)

For methods other than event handlers use "Task" instead:
    private async Task UpdateAsync()

More information in the related documentation: https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-return-types#void-return-type

## Additional resources

- For usage examples, see [examples.md](examples.md)
