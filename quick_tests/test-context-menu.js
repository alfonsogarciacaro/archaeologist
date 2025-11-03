// Test script to verify context menu functionality
// This would be run in the browser console

console.log('Testing context menu...');

// Simulate right-click on a node
const nodes = document.querySelectorAll('.react-flow__node');
if (nodes.length > 0) {
    const firstNode = nodes[0];
    
    // Create and dispatch right-click event
    const rightClickEvent = new MouseEvent('contextmenu', {
        bubbles: true,
        cancelable: true,
        clientX: firstNode.getBoundingClientRect().left + 50,
        clientY: firstNode.getBoundingClientRect().top + 50,
        button: 2
    });
    
    firstNode.dispatchEvent(rightClickEvent);
    
    // Check if context menu appears
    setTimeout(() => {
        const contextMenu = document.querySelector('.context-menu');
        if (contextMenu && contextMenu.style.display !== 'none') {
            console.log('✅ Context menu appears successfully');
            
            // Try clicking on metadata item
            const metadataItem = contextMenu.querySelector('.context-menu-item:not(.delete)');
            if (metadataItem) {
                metadataItem.click();
                
                setTimeout(() => {
                    const modal = document.querySelector('.modal-backdrop');
                    if (modal && modal.style.display !== 'none') {
                        console.log('✅ Metadata modal appears successfully');
                    } else {
                        console.log('❌ Metadata modal does not appear');
                    }
                }, 100);
            }
        } else {
            console.log('❌ Context menu does not appear');
        }
    }, 100);
} else {
    console.log('❌ No nodes found to test with');
}