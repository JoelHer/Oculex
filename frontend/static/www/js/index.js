const image = document.getElementById('image');
const selectionBox = document.getElementById('selection-box');
const coordinatesDisplay = document.getElementById('coordinates');

let startX, startY, isSelecting = false;

let counter = 1;
let selectedItem = null;
let boxes = [];
let unsavedBoxes = new Set();

class ChangeableBox {
    constructor(id) {
        this.id = id;
        this.box_left = 0;
        this.box_top = 0;
        this.box_width = 0;
        this.box_height = 0;
    }

    // Methode zum Erstellen des Listenelements
    createElement() {
        const li = document.createElement("li");

        const idElement = document.createElement("span");
        idElement.textContent = `ID: ${this.id}`; // ID anzeigen
        
        const boxLeftElement = document.createElement("span");
        boxLeftElement.textContent = `Left: ${this.box_left}`;
        
        const boxTopElement = document.createElement("span");
        boxTopElement.textContent = `Top: ${this.box_top}`;
        
        const boxWidthElement = document.createElement("span");
        boxWidthElement.textContent = `Width: ${this.box_width}`;
        
        const boxHeightElement = document.createElement("span");
        boxHeightElement.textContent = `Height: ${this.box_height}`;
        
        // Entfernen-Button
        const removeButton = document.createElement("button");
        removeButton.classList.add("remove-button");
        removeButton.innerHTML = '<span class="material-icons">delete</span>';
        removeButton.onclick = () => this.remove(li);
        
        // Auswahl-Button
        const selectButton = document.createElement("button");
        selectButton.textContent = "Use Selection";
        selectButton.classList.add("use-selection", "hidden");
        selectButton.onclick = () => this.select(li);

        // Füge die Elemente zum Listeneintrag hinzu
        li.appendChild(idElement); // ID-Element hinzufügen
        li.appendChild(boxLeftElement);
        li.appendChild(boxTopElement);
        li.appendChild(boxWidthElement);
        li.appendChild(boxHeightElement);
        li.appendChild(removeButton);
        li.appendChild(selectButton);
        li.dataset.id = this.id;
        
        return li;
    }

    // Methode zum Entfernen eines Elements
    remove(li) {
        li.remove();
        if (selectedItem === li) {
            selectedItem = null;
        }
        boxes = boxes.filter(box => box.id !== this.id);
        unsavedBoxes.delete(this.id);
        saveSettings()
        this.removeVisualFeedback();
    }

    // Methode zum Auswählen eines Elements
    select(li) {
        li.classList.toggle("selected");
        if (li.classList.contains("selected")) {
            selectedItem = li;
            this.updateBoxWithSelection();
            selectionBox.style.display = 'none'; // Hide the active selection
            saveSettings(); // Save the boxes when selecting
        } else {
            selectedItem = null;
        }
    }

    updateBoxWithSelection() {
        const rect = image.getBoundingClientRect();
        const boxRect = selectionBox.getBoundingClientRect();

        this.box_left = Math.round((boxRect.left - rect.left) / rect.width * image.naturalWidth);
        this.box_top = Math.round((boxRect.top - rect.top) / rect.height * image.naturalHeight);
        this.box_width = Math.round((boxRect.width / rect.width) * image.naturalWidth);
        this.box_height = Math.round((boxRect.height / rect.height) * image.naturalHeight);

        this.updateElement();
    }

    updateElement() {
        const li = document.querySelector(`li[data-id='${this.id}']`);
        li.querySelector("span:nth-child(2)").textContent = `Left: ${this.box_left} | `;
        li.querySelector("span:nth-child(3)").textContent = `Top: ${this.box_top} | `;
        li.querySelector("span:nth-child(4)").textContent = `Width: ${this.box_width} | `;
        li.querySelector("span:nth-child(5)").textContent = `Height: ${this.box_height} | `;
    }
}

function addItem() {
    const rect = image.getBoundingClientRect();
    const boxRect = selectionBox.getBoundingClientRect();

    // Check if there is an active selection
    const hasSelection = selectionBox.style.display === 'block' && boxRect.width > 0 && boxRect.height > 0;

    const item = new ChangeableBox(counter);

    
    if (hasSelection) {
        // Use the current selection for the new box
        item.box_left = Math.round((boxRect.left - rect.left) / rect.width * image.naturalWidth);
        item.box_top = Math.round((boxRect.top - rect.top) / rect.height * image.naturalHeight);
        item.box_width = Math.round((boxRect.width / rect.width) * image.naturalWidth);
        item.box_height = Math.round((boxRect.height / rect.height) * image.naturalHeight);
        
        // Hide the selection box after using it
        selectionBox.style.display = 'none';
    }

    
    
    const li = item.createElement();
    document.getElementById("itemList").appendChild(li);
    boxes.push(item);
    counter++;
    saveSettings()

    const useSelectionButtons = document.querySelectorAll('.use-selection');
    useSelectionButtons.forEach(button => button.classList.add('hidden'));
}

function loadSettings() {
    const selection = document.getElementById("selection");
    const handle = document.querySelector(".resize-handle");
    const brightnessInput = document.getElementById("brightness");
    const contrastInput = document.getElementById("contrast");
    const rotationInput = document.getElementById("rotation"); // Add rotation input
    const cropInputs = {
        top: document.getElementById("crop_top"),
        bottom: document.getElementById("crop_bottom"),
        left: document.getElementById("crop_left"),
        right: document.getElementById("crop_right")
    };

    fetch("/get_settings/a")
        .then(response => response.json())
        .then(settings => {
            brightnessInput.value = settings.brightness;
            contrastInput.value = settings.contrast;
            rotationInput.value = settings.rotation; // Load rotation value
            cropInputs.top.value = settings.crop_top;
            cropInputs.bottom.value = settings.crop_bottom;
            cropInputs.left.value = settings.crop_left;
            cropInputs.right.value = settings.crop_right;
        });
    fetch("/get_boxes/a")
        .then(response => response.json())
        .then(data => {
            data.forEach(boxData => {
                const item = new ChangeableBox(boxData.id);
                item.box_left = boxData.box_left;
                item.box_top = boxData.box_top;
                item.box_width = boxData.box_width;
                item.box_height = boxData.box_height;
                const li = item.createElement();
                document.getElementById("itemList").appendChild(li);
                boxes.push(item);
                counter = Math.max(counter, boxData.id + 1);
            });
        });
}

let updateTimeInterval;

function saveSettings() {
    const spinnerOverlay = document.getElementById("spinner-overlay");
    spinnerOverlay.classList.add("show"); // Show spinner with fade-in effect

    const selection = document.getElementById("selection");
    const handle = document.querySelector(".resize-handle");
    const brightnessInput = document.getElementById("brightness");
    const contrastInput = document.getElementById("contrast");
    const rotationInput = document.getElementById("rotation"); // Add rotation input
    const cropInputs = {
        top: document.getElementById("crop_top"),
        bottom: document.getElementById("crop_bottom"),
        left: document.getElementById("crop_left"),
        right: document.getElementById("crop_right")
    };

    const rect = image.getBoundingClientRect();
    const boxRect = selectionBox.getBoundingClientRect();

    const box_left = (boxRect.left - rect.left) / rect.width * image.naturalWidth;
    const box_top = (boxRect.top - rect.top) / rect.height * image.naturalHeight;
    const box_width = (boxRect.width / rect.width) * image.naturalWidth;
    const box_height = (boxRect.height / rect.height) * image.naturalHeight;

    const settings = {
        box_top: Math.round(box_top),
        box_left: Math.round(box_left),
        box_width: Math.round(box_width),
        box_height: Math.round(box_height),
        brightness: parseFloat(brightnessInput.value),
        contrast: parseFloat(contrastInput.value),
        rotation: parseInt(rotationInput.value), // Save rotation value
        crop_top: Math.round(parseInt(cropInputs.top.value)),
        crop_bottom: Math.round(parseInt(cropInputs.bottom.value)),
        crop_left: Math.round(parseInt(cropInputs.left.value)),
        crop_right: Math.round(parseInt(cropInputs.right.value)),
    };

    fetch("/set_settings/a", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
    }).then(() => {
        console.log("Settings saved:", settings);
        document.getElementById("image").src = "/snapshot/a" + "?" + new Date().getTime();
    });

    fetch("/set_boxes/a", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boxes.map(box => ({
            id: box.id,
            box_left: box.box_left,
            box_top: box.box_top,
            box_width: box.box_width,
            box_height: box.box_height
        })))
    }).then(() => {
        console.log("Boxes saved:", boxes);
        document.getElementById("image").src = "/snapshot/a" + "?" + new Date().getTime();
    }).finally(() => {
        setTimeout(() => {
            spinnerOverlay.classList.remove("show"); // Hide spinner with fade-out effect
        }, 500); // Delay to ensure the image is updated before hiding the spinner
    });
}

function reloadImage() {
    const spinnerOverlay = document.getElementById("spinner-overlay");
    const spinnerOverlayp = document.getElementById("spinner-overlay-p");
    spinnerOverlayp.classList.add("show"); // Show spinner with fade-in effect
    spinnerOverlay.classList.add("show"); // Show spinner with fade-in effect
    document.getElementById("image").src = "/snapshot/a" + "?" + new Date().getTime();
    document.getElementById("image-p").src = "/computed/a" + "?" + new Date().getTime();
}

document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    const spinnerOverlay = document.getElementById("spinner-overlay");
    const spinnerOverlayp = document.getElementById("spinner-overlay-p");
    spinnerOverlay.classList.add("show"); // Show spinner on page load
    spinnerOverlayp.classList.add("show"); // Show spinner on page load
});

document.addEventListener('DOMContentLoaded', function() {
    const useSelectionButton = document.querySelector('.use-selection');
    const selectionBox = document.querySelector('.selection-box');
    let isSelecting = false;
    let startX, startY;

    const image = document.getElementById('image');

    image.addEventListener('mousedown', (e) => {
        const rect = image.getBoundingClientRect();
        startX = e.clientX - rect.left;
        startY = e.clientY - rect.top;
        isSelecting = true;

        selectionBox.style.left = `${startX}px`;
        selectionBox.style.top = `${startY}px`;
        selectionBox.style.width = '0';
        selectionBox.style.height = '0';
        selectionBox.style.display = 'block';
    });

    image.addEventListener('mousemove', (e) => {
        if (!isSelecting) return;

        const rect = image.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        const width = currentX - startX;
        const height = currentY - startY;

        selectionBox.style.width = Math.abs(width) + 'px';
        selectionBox.style.height = Math.abs(height) + 'px';
        
        if (width < 0) {
            selectionBox.style.left = `${currentX}px`;
        }

        if (height < 0) {
            selectionBox.style.top = `${currentY}px`;
        }
    });

    image.addEventListener('mouseup', () => {
        isSelecting = false;
        //remove the "hidden" class from every button that has the use-selection class
        const useSelectionButtons = document.querySelectorAll('.use-selection');
        useSelectionButtons.forEach(button => button.classList.remove('hidden'));
    });

    image.addEventListener('mouseleave', () => {
        isSelecting = false;
    });
});

function hideSpinner() {
    const spinnerOverlay = document.getElementById("spinner-overlay");
    spinnerOverlay.classList.remove("show"); // Hide spinner when image is loaded
}

function hideSpinnerP() {
    const spinnerOverlay = document.getElementById("spinner-overlay-p");
    spinnerOverlay.classList.remove("show"); // Hide spinner when image is loaded
}

function onImageUpdated() {
    console.log("Image has been updated");
    const loadingText = document.querySelector(".loading-text");
    let lastUpdated = new Date();

    if (updateTimeInterval) {
        clearInterval(updateTimeInterval);
    }

    updateTimeInterval = setInterval(() => {
        const now = new Date();
        const seconds = Math.floor((now - lastUpdated) / 1000);
        loadingText.textContent = `Updated ${seconds} seconds ago`;
    }, 1000);
}


