import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw
import requests
from io import BytesIO


def fetch_pokemon_list():
    """Fetch the list of Pokémon names from the PokéAPI."""
    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=10000")
        response.raise_for_status()
        data = response.json()
        pokemon_list = [pokemon['name'] for pokemon in data['results']]
        return pokemon_list
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch Pokémon list: {e}")
        return []

def create_placeholder_image(size=(350, 350), text=""):
    """Create a placeholder image with specified size and text."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    # Calculate the size of the text using textbbox
    text_bbox = draw.textbbox((0, 0), text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Center the text in the image
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(text_position, text, fill="black")

    return img

def fetch_pokemon_data():
    """Fetch Pokémon details and update the UI."""
    pokemon_name = entry_name.get().strip().lower()
    if not pokemon_name:
        messagebox.showerror("Error", "Please enter a Pokémon name!")
        return

    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}")
        response.raise_for_status()
        data = response.json()

        # Extract relevant details
        pokemon_id = data['id']
        types = [t['type']['name'] for t in data['types']]
        sprite_url = data['sprites']['front_default']
        stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}

        # Update UI with the fetched data
        label_stats_id.config(text=f"ID: {pokemon_id}")
        label_stats_types.config(text=f"Types: {', '.join(types)}")

        # Calculate manual padding for consistent alignment
        max_stat_length = max(len(stat) for stat in stats.keys())
        stats_text = "\n".join([f"{stat:<{max_stat_length}} : {value}" for stat, value in stats.items()])

        # Update the label with the current font
        label_stats.config(text=f"Stats:\n{stats_text}", font=font_settings)

        # Fetch and display the Pokémon image or use the placeholder if unavailable
        if sprite_url:
            image_response = requests.get(sprite_url)
            image_response.raise_for_status()
            image_data = Image.open(BytesIO(image_response.content))
            image_data = image_data.resize((350, 350), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image_data)
            label_image.config(image=photo)
            label_image.image = photo
        else:
            # Keep the placeholder image if no sprite is available
            label_image.config(image=placeholder_photo)

        # Display the "Show Different Types" button
        btn_show_different_types.grid(row=3, column=0, pady=10, padx=10, sticky="w")

        # Store the Pokémon data in a global variable for later use
        global pokemon_data
        pokemon_data = data

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")
    except KeyError:
        messagebox.showerror("Error", "Pokémon not found!")

def show_different_types():
    """Show different forms (shiny, evolutions) of the Pokémon in order."""
    if not pokemon_data:
        messagebox.showerror("Error", "No Pokémon data available!")
        return

    pokemon_name = pokemon_data['name']
    shiny_url = pokemon_data.get('sprites', {}).get('front_shiny')
    species_url = pokemon_data.get('species', {}).get('url')  # URL for evolution data
    evolution_chain_url = None

    # Fetch Evolution Chain URL from species
    if species_url:
        response = requests.get(species_url)
        species_data = response.json()
        evolution_chain_url = species_data.get('evolution_chain', {}).get('url')

    # Create new window for displaying forms
    new_window = tk.Toplevel(root)
    new_window.title(f"{pokemon_name.capitalize()} - Forms")

    row_offset = 0
    col_offset = 0
    shown_pokemon = set()  # Track the Pokémon we have already shown to avoid duplicates

    # Show shiny form first
    if shiny_url:
        response = requests.get(shiny_url)
        image_data = Image.open(BytesIO(response.content))
        image_data = image_data.resize((350, 350), Image.Resampling.LANCZOS)
        photo_shiny = ImageTk.PhotoImage(image_data)
        label_shiny = tk.Label(new_window, image=photo_shiny)
        label_shiny.image = photo_shiny
        label_shiny.grid(row=row_offset, column=col_offset, padx=10, pady=10)
        shiny_label = tk.Label(new_window, text="Shiny Form", font=font_settings, fg='black')
        shiny_label.grid(row=row_offset + 1, column=col_offset, pady=5)
        col_offset += 1

    
    # Show evolutions in order (including the selected Pokémon itself)
    if evolution_chain_url:
        response = requests.get(evolution_chain_url)
        evolution_data = response.json()

        # Get evolutions in the correct order
        evolution_names = extract_evolutions(evolution_data['chain'], shown_pokemon)

        # Display the evolutions, including the selected Pokémon
        for evolution in evolution_names:
            show_evolution(new_window, evolution, row_offset, col_offset)
            col_offset += 1  # Move to the next column for the next evolution


def show_pokemon(window, pokemon_name, row_offset, col_offset, shown_pokemon):
    """Fetch and display the selected Pokémon's image and name."""
    # Fetch Pokémon sprite URL if available
    pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    response = requests.get(pokemon_url)
    pokemon_data = response.json()
    pokemon_sprite_url = pokemon_data.get('sprites', {}).get('front_default')

    if pokemon_sprite_url:
        response = requests.get(pokemon_sprite_url)
        image_data = Image.open(BytesIO(response.content))
        image_data = image_data.resize((350, 350), Image.Resampling.LANCZOS)
        photo_pokemon = ImageTk.PhotoImage(image_data)
        label_pokemon = tk.Label(window, image=photo_pokemon)
        label_pokemon.image = photo_pokemon
        label_pokemon.grid(row=row_offset, column=col_offset, padx=10, pady=10)

    pokemon_label = tk.Label(window, text=f"{pokemon_name.capitalize()}", font=font_settings, fg='black')
    pokemon_label.grid(row=row_offset + 1, column=col_offset, pady=5)

def extract_evolutions(chain, shown_pokemon):
    """Extract evolutions from the evolution chain and ensure correct order (including previous, current, and next evolutions)."""
    evolutions = []  # List to store the evolution chain in correct order
    
    # First, we add the base Pokémon that was selected (this is critical to show Charmander before Charmeleon)
    if chain['species']['name'] not in shown_pokemon:
        evolutions.append(chain['species']['name'])
        shown_pokemon.add(chain['species']['name'])  # Add the base Pokémon to the set of shown Pokémon
    
    # Now, we handle the evolutions. The first evolution should always appear after the base Pokémon.
    if 'evolves_to' in chain:
        for evolution in chain['evolves_to']:
            if evolution['species']['name'] not in shown_pokemon:  # Only add if not already shown
                evolutions.append(evolution['species']['name'])
                shown_pokemon.add(evolution['species']['name'])  # Add to the set of shown Pokémon
                # Recursively add future evolutions
                evolutions.extend(extract_evolutions(evolution, shown_pokemon))
    
    return evolutions


def show_evolution(window, evolution_name, row_offset, col_offset):
    """Fetch and display an evolution's image and name."""
    # Fetch evolution sprite URL if available
    evolution_url = f"https://pokeapi.co/api/v2/pokemon/{evolution_name}"
    response = requests.get(evolution_url)
    evolution_data = response.json()
    evolution_sprite_url = evolution_data.get('sprites', {}).get('front_default')

    if evolution_sprite_url:
        response = requests.get(evolution_sprite_url)
        image_data = Image.open(BytesIO(response.content))
        image_data = image_data.resize((350, 350), Image.Resampling.LANCZOS)
        photo_evolution = ImageTk.PhotoImage(image_data)
        label_evolution = tk.Label(window, image=photo_evolution)
        label_evolution.image = photo_evolution
        label_evolution.grid(row=row_offset, column=col_offset, padx=10, pady=10)

    evolution_label = tk.Label(window, text=f"{evolution_name.capitalize()} Evolution", font=font_settings, fg='black')
    evolution_label.grid(row=row_offset + 1, column=col_offset, pady=5)



def on_listbox_select(event):
    """Handle Listbox selection and fetch Pokémon details."""
    try:
        selection = listbox.get(listbox.curselection())
        entry_name.delete(0, tk.END)
        entry_name.insert(0, selection)
        fetch_pokemon_data()
    except tk.TclError:
        pass  # Ignore empty selection errors

def show_main_page():
    """Hide the main menu and show the Pokémon Finder page."""
    frame_menu.grid_forget()  # Hide the menu frame
    
    # Set the positions for input, listbox, and display sections
    frame_input.grid(row=1, column=1, padx=10, pady=10, sticky="nw")  # Search bar and button to the right of stats
    frame_listbox.grid(row=2, column=1, padx=10, pady=10, sticky="nw")  # Listbox below the search bar
    frame_display.grid(row=1, column=0, rowspan=2, padx=10, pady=10)  # Display frame spans two rows on the left
    
    # Show the back button on the Pokémon Finder page (positioned at the top left)
    frame_back_button.grid(row=0, column=0, pady=10, padx=10, sticky="nw")  # Positioned top-left above the content

def show_main_menu():
    """Show the main menu and hide other sections."""
    # Hide the main page UI elements
    frame_input.grid_forget()
    frame_listbox.grid_forget()
    frame_display.grid_forget()

    # Show the main menu frame
    frame_menu.grid(row=0, column=0, sticky="nsew")
    
    # Hide the back button when on the main menu
    frame_back_button.grid_forget()

# GUI Setup
root = tk.Tk()
root.title("Pokémon Finder")
root.geometry("1100x500")
root.configure(bg='#d01e36')
root.resizable(False, False)  # Ensure the window is non-resizable


font_settings = ("Gill Sans", 15, "bold")

# Placeholder image
placeholder_img = create_placeholder_image()
placeholder_photo = ImageTk.PhotoImage(placeholder_img)

# Fetch Pokémon list before populating the listbox
pokemon_list = fetch_pokemon_list()

# Main Menu

# Frame Setup (Use grid for the menu frame)
frame_menu = tk.Frame(root, bg='#d01e36')
frame_menu.grid(row=0, column=0, sticky="nsew")

# Configure row and column weights to allow expansion
frame_menu.grid_rowconfigure(0, weight=1)  # Allow the row to expand
frame_menu.grid_columnconfigure(0, weight=1)  # Allow the column to expand

# Label setup
label_menu = tk.Label(frame_menu, text="Pokedex", font=font_settings, fg='white', bg='#d01e36')
label_menu.grid(row=0, column=0, padx=500, pady=150, sticky="nsew")  # Sticky ensures centering

# Button setup
btn_go_to_main_page = tk.Button(frame_menu, text="Open", font=font_settings, command=show_main_page, bg='green', fg='white', highlightthickness=0)
btn_go_to_main_page.grid(row=1, column=0, padx=500, sticky="nsew")  # Center the button


# Add a back button to the Pokémon Finder page (it will only be visible on the Pokémon Finder page)
frame_back_button = tk.Frame(root, bg='#d01e36')
frame_back_button.grid_forget()  # Hide initially

# Place the actual button inside the back button frame
btn_back_to_menu = tk.Button(
    frame_back_button, 
    text="Back", 
    font=font_settings, 
    command=show_main_menu, 
    bg='green', 
    fg='white', 
    highlightthickness=0
)
btn_back_to_menu.grid(row=0, column=0, pady=5, padx=5)

frame_input = tk.Frame(root, bg='#d01e36')

# Search bar and search button for Pokémon name
entry_name = tk.Entry(frame_input, font=font_settings)
entry_name.grid(row=0, column=0, padx=10, sticky="w")

btn_search = tk.Button(frame_input, text="Search", font=font_settings, command=fetch_pokemon_data, bg='green', fg='white', highlightthickness=0)
btn_search.grid(row=0, column=1, padx=10, sticky="w")

# Listbox for Pokémon selection (Initially hidden)
frame_listbox = tk.Frame(root, bg='#d01e36', height=350)
frame_listbox.grid_forget()  # Hide the listbox initially

listbox = tk.Listbox(frame_listbox, height=10, width=30, font=font_settings, fg='black', bg='white')
listbox.grid(row=0, column=0, padx=10, pady=10)  # Using grid instead of pack
listbox.bind("<<ListboxSelect>>", on_listbox_select)

# Populate the Listbox with Pokémon names
for pokemon in pokemon_list:
    listbox.insert(tk.END, pokemon)

# Display section (Initially hidden)
frame_display = tk.Frame(root, bg='#d01e36')

# Image and details side by side
frame_image_text = tk.Frame(frame_display, bg='#d01e36')
frame_image_text.grid(row=0, column=0)

# Image label (Left Column)
label_image = tk.Label(frame_image_text, bg='white', image=placeholder_photo)
label_image.grid(row=0, column=0, padx=10)

# Stats frame (Middle Column)
frame_stats = tk.Frame(frame_image_text, bg='#d01e36', height=350, width=200)
frame_stats.grid(row=0, column=1, padx=10, sticky="n")


# ID label inside the middle column
label_stats_id = tk.Label(
    frame_stats, 
    text="ID: Not Available", 
    font=font_settings, 
    fg='white', 
    bg='#d01e36', 
    anchor="w", 
    justify="left", 
    width=20  # Set a fixed width
)
label_stats_id.grid(row=0, column=0, pady=5)

# Types (element) label inside the middle column
label_stats_types = tk.Label(
    frame_stats, 
    text="Types: Not Available", 
    font=font_settings, 
    fg='white', 
    bg='#d01e36', 
    anchor="w", 
    justify="left", 
    width=20  # Set a fixed width
)
label_stats_types.grid(row=1, column=0, pady=5)

# Stats label inside the middle column
label_stats = tk.Label(
    frame_stats, 
    text="Stats: Not Available", 
    font=font_settings, 
    fg='white', 
    bg='#d01e36', 
    anchor="w", 
    justify="left", 
    width=20  # Set a fixed width
)
label_stats.grid(row=2, column=0, pady=10)

# Different Types Button (Initially hidden)
btn_show_different_types = tk.Button(
    frame_stats, 
    text="Show Different Types", 
    font=font_settings, 
    command=show_different_types, 
    bg='green', 
    fg='white', 
    highlightthickness=0
)
btn_show_different_types.grid_forget()  # Hidden initially

# Details frame (Right Column)
frame_details = tk.Frame(frame_image_text, bg='red')
frame_details.grid(row=0, column=2, padx=10, sticky="nw")

# Run the application
root.mainloop()
