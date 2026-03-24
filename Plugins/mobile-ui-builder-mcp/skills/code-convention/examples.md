Following is an example of how properties and methods should be declared:

public class Example
{
    // Injections
    [Inject]
    public Manager Manager {get; set;}

    // Public properties
    public string Mobile {get; set;}

    public string Name
    {
        set
        {
            _name = value;
        }
    }

    // Private properties
    private int Age;

    // See Note 3 below
    private string _name;

    // constructor
    public Example(IntPtr handle) : base(handle)
    {
    }

    // public methods
    public UpdateValue(int age)
    {
        Age = age;
    }

    // private methods
    private SetView()
    {
        ...
    }

    // async methods
    private async Task UpdateDataAsync()
    {
        await DownloadData();
    }
}
