Scripts used to create the engineering thesis. The project concerned the creation of a high-rise building with the use of modern design technologies. The building was designed based on the principles of generative and parametric design.

# Space planning test model

The `room_data.json` file specifies the problem definition including room sizes and adjacency criteria. To create a space plan import the `get_layout` function from the `space_planning` library. The function expects 5 inputs (n represents the number of rooms specified in the problem definition):

- room_def: problem definition imported from `room_data.json` file
- split_list: list of (n-2) floats in domain [0.0-1.0] which determines the order of the subdivision tree
- dir_list: list of (n-1) boolean variables [0 or 1] which determines the direction of each split
- room_order: an ordering of (n) sequential integers starting at 0 which determines room assignment
- min_opening: the minimum size of connections between rooms and to the outside (for example the width of a door)

The function generates 3 outputs:

- the walls as lines represented by its endpoints [[x1, y1], [x2, y2]]
- the adjacency score as number of adjacency rules broken (0 represents a perfect design) - this should be minimized during optimization
- the aspect score as deviation from expected aspect ratios (0.0 represents perfect aspect match) - this should be minimized during optimization

![analizy](https://user-images.githubusercontent.com/49916782/115149775-ecce0d80-a065-11eb-872a-3d10d4876a2b.jpg)
![wizualizacja](https://user-images.githubusercontent.com/49916782/115149866-49c9c380-a066-11eb-8d37-f476c212d68b.jpg)
![Mieszkalne](https://user-images.githubusercontent.com/49916782/115149801-07a08200-a066-11eb-9bfe-ae544f639f90.jpg)
![Biura](https://user-images.githubusercontent.com/49916782/115149793-00797400-a066-11eb-8a88-e8f2e7d48dc6.jpg)
![Zagospodarowanie](https://user-images.githubusercontent.com/49916782/115149820-19822500-a066-11eb-8019-404720f0285c.jpg)
![Mapa sytuacyjna z siatką bez tła](https://user-images.githubusercontent.com/49916782/115149835-24d55080-a066-11eb-9950-95b42ffcc59b.jpg)

